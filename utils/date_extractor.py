import regex
import re
import json
import datetime
import dateutil.parser as dparser
import logging

logger = logging.getLogger(__name__)

class DateExtractor:
    """Handles extraction and parsing of posting dates from web content"""
    
    def __init__(self):
        self.today = datetime.date.today()
        
        # Multiple patterns to search for date fields
        self.date_field_patterns = [
            r'"datePosted":\s*"([^"]+)"',
            r'"publishedDate":\s*"([^"]+)"',
            r'"createdDate":\s*"([^"]+)"',
            r'"postingDate":\s*"([^"]+)"',
            r'"date_posted":\s*"([^"]+)"',
            r'"posted_date":\s*"([^"]+)"',
            r'"dateCreated":\s*"([^"]+)"',
            r'"created":\s*"([^"]+)"',
            r'"published":\s*"([^"]+)"'
        ]

    def extract_date_from_content(self, content):
        """Extract posting date from page content using multiple methods"""
        logger.info("Searching for posting date in page content...")
        
        # Method 1: Search for meta tags with itemprop="datePosted"
        date_info = self.search_meta_tags(content)
        if date_info:
            return date_info
        
        # Method 2: Search for structured data (JSON-LD)
        date_info = self.search_structured_data(content)
        if date_info:
            return date_info
        
        # Method 3: Search line by line for date patterns
        date_info = self.search_line_patterns(content)
        if date_info:
            return date_info
        
        # Method 4: Search for common date formats in text
        date_info = self.search_text_patterns(content)
        if date_info:
            return date_info
        
        logger.warning("No posting date found in page content")
        return None

    def search_meta_tags(self, content):
        """Search for dates in meta tags with itemprop or name attributes"""
        try:
            # Pattern for meta tags with datePosted itemprop
            meta_patterns = [
                r'<meta\s+itemprop=["\']datePosted["\'][^>]*content=["\']([^"\']+)["\'][^>]*/?>', 
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*itemprop=["\']datePosted["\'][^>]*/?>', 
                r'<meta\s+name=["\']datePosted["\'][^>]*content=["\']([^"\']+)["\'][^>]*/?>', 
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']datePosted["\'][^>]*/?>', 
                r'<meta\s+name=["\']date["\'][^>]*content=["\']([^"\']+)["\'][^>]*/?>', 
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']date["\'][^>]*/?>', 
                r'<meta\s+property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\'][^>]*/?>', 
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']article:published_time["\'][^>]*/?>'
            ]
            
            found_dates = []
            
            for pattern in meta_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if matches:
                    for date_value in matches:
                        # Try to parse and convert PDF date format if needed
                        processed_date = self.process_date_format(date_value)
                        if processed_date:
                            found_dates.append({
                                'date': processed_date, 
                                'source': f'Meta tag pattern: {pattern}',
                                'original': date_value
                            })
            
            if found_dates:
                # If multiple dates found, prefer the one in the past
                best_date = self.select_best_date(found_dates)
                if best_date:
                    logger.info(f"Found date in meta tag: {best_date['date']} (original: {best_date['original']})")
                    return best_date
                    
        except Exception as e:
            logger.debug(f"Error searching meta tags: {e}")
        
        return None

    def search_structured_data(self, content):
        """Search for dates in JSON-LD structured data"""
        try:
            # Find JSON-LD script tags
            json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            json_scripts = re.findall(json_ld_pattern, content, re.DOTALL | re.IGNORECASE)
            
            found_dates = []
            
            for script in json_scripts:
                try:
                    data = json.loads(script.strip())
                    if isinstance(data, dict):
                        date_value = self.find_date_in_json(data)
                        if date_value:
                            found_dates.append({
                                'date': date_value, 
                                'source': 'JSON-LD structured data',
                                'original': date_value
                            })
                except json.JSONDecodeError:
                    continue
            
            if found_dates:
                # If multiple dates found, prefer the one in the past
                best_date = self.select_best_date(found_dates)
                if best_date:
                    logger.info(f"Found date in JSON-LD: {best_date['date']} (original: {best_date['original']})")
                    return best_date
                    
        except Exception as e:
            logger.debug(f"Error searching structured data: {e}")
        
        return None

    def find_date_in_json(self, data, keys_to_check=None):
        """Recursively search for date fields in JSON data"""
        if keys_to_check is None:
            keys_to_check = ['datePosted', 'publishedDate', 'createdDate', 'postingDate', 
                           'date_posted', 'posted_date', 'dateCreated', 'created', 'published',
                           'datePublished', 'dateModified', 'dateUpdated', 'lastModified']
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key in keys_to_check and isinstance(value, str):
                    return value
                elif isinstance(value, (dict, list)):
                    result = self.find_date_in_json(value, keys_to_check)
                    if result:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self.find_date_in_json(item, keys_to_check)
                if result:
                    return result
        
        return None

    def search_line_patterns(self, content):
        """Search for date patterns line by line"""
        for line in content.split('\n'):
            for pattern in self.date_field_patterns:
                match = regex.search(pattern, line, regex.IGNORECASE)
                if match:
                    date_value = match.group(1)
                    logger.info(f"Found date pattern: {date_value}")
                    return {'date': date_value, 'source': f'Pattern match: {pattern}'}
        
        return None

    def search_text_patterns(self, content):
        """Search for common date formats in plain text"""
        # Common date patterns
        date_patterns = [
            r'posted[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'published[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'created[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})',
            r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s*[+-]\d{4}',
            r'D:(\d{14}[+-]\d{2}\'?\d{2}\'?)',  # PDF date format
        ]
        
        found_dates = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches:
                    date_value = match if isinstance(match, str) else match[0]
                    
                    # Process PDF dates
                    if pattern.startswith('D:'):
                        date_value = f"D:{date_value}"
                    
                    processed_date = self.process_date_format(date_value)
                    if processed_date:
                        found_dates.append({
                            'date': processed_date, 
                            'source': f'Text pattern: {pattern}',
                            'original': date_value
                        })
        
        if found_dates:
            # If multiple dates found, prefer the one in the past
            best_date = self.select_best_date(found_dates)
            if best_date:
                logger.info(f"Found date in text: {best_date['date']} (original: {best_date['original']})")
                return best_date
        
        return None

    def process_date_format(self, date_value):
        """Process and convert various date formats"""
        try:
            # Handle PDF date format: D:20250804000000+01'00'
            if date_value.startswith('D:'):
                # Extract the date part: D:20250804000000+01'00' -> 20250804000000+01'00'
                date_part = date_value[2:]
                # Remove the apostrophe: 20250804000000+01'00' -> 20250804000000+0100
                date_part = date_part.replace("'", "")
                
                # Parse the date: YYYYMMDDHHMMSS+HHMM format
                if len(date_part) >= 14:
                    year = date_part[0:4]
                    month = date_part[4:6]
                    day = date_part[6:8]
                    hour = date_part[8:10]
                    minute = date_part[10:12]
                    second = date_part[12:14]
                    
                    # Construct ISO format
                    iso_date = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
                    
                    # Add timezone if present
                    if len(date_part) > 14 and ('+' in date_part[14:] or '-' in date_part[14:]):
                        tz_part = date_part[14:]
                        if len(tz_part) >= 5:
                            tz_hours = tz_part[1:3]
                            tz_minutes = tz_part[3:5]
                            iso_date += f"{tz_part[0]}{tz_hours}:{tz_minutes}"
                    
                    logger.debug(f"Converted PDF date '{date_value}' to ISO format: '{iso_date}'")
                    return iso_date
            
            # Return original date for other formats
            return date_value
            
        except Exception as e:
            logger.debug(f"Error processing date format '{date_value}': {e}")
            return date_value

    def select_best_date(self, date_candidates):
        """Select the best date from multiple candidates, preferring past dates"""
        try:
            valid_dates = []
            
            for candidate in date_candidates:
                try:
                    parsed_date = dparser.parse(candidate['date'], fuzzy=True)
                    candidate['parsed'] = parsed_date
                    candidate['days_from_today'] = (self.today - parsed_date.date()).days
                    valid_dates.append(candidate)
                except Exception as e:
                    logger.debug(f"Could not parse candidate date '{candidate['date']}': {e}")
                    continue
            
            if not valid_dates:
                return None
            
            # Separate past and future dates
            past_dates = [d for d in valid_dates if d['days_from_today'] >= 0]
            future_dates = [d for d in valid_dates if d['days_from_today'] < 0]
            
            # Prefer past dates
            if past_dates:
                # Among past dates, prefer the most recent one (smallest positive days_from_today)
                best_date = min(past_dates, key=lambda x: x['days_from_today'])
                logger.info(f"Selected past date: {best_date['date']} ({best_date['days_from_today']} days ago)")
                return best_date
            elif future_dates:
                # If only future dates available, select the closest to today
                best_date = max(future_dates, key=lambda x: x['days_from_today'])
                logger.info(f"Only future dates available, selected: {best_date['date']} ({abs(best_date['days_from_today'])} days ahead)")
                return best_date
            
        except Exception as e:
            logger.debug(f"Error selecting best date: {e}")
        
        # Fallback to first valid date
        if date_candidates:
            return date_candidates[0]
        
        return None

    def parse_date(self, date_string):
        """Parse date string into datetime object"""
        try:
            # Try parsing with dateutil (handles most formats)
            parsed_date = dparser.parse(date_string, fuzzy=True)
            logger.info(f"Successfully parsed date: {parsed_date}")
            return parsed_date
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to parse date '{date_string}': {e}")
            return None

    def calculate_days_since_posted(self, parsed_date):
        """Calculate days since the job was posted"""
        try:
            posting_date = parsed_date.date()
            days_since = (self.today - posting_date).days
            logger.info(f"Job posted {days_since} days ago")
            return days_since
        except Exception as e:
            logger.error(f"Error calculating days since posted: {e}")
            return None
