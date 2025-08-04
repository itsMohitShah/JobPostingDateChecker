import requests
import regex
import datetime
import dateutil.parser as dparser
import logging
import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import re
from urllib.parse import urlparse
import sys
from skills_analyzer import SkillsAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_posting_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobPostingDateChecker:
    def __init__(self):
        self.today = datetime.date.today()
        self.max_age_days = 7  # Don't apply if older than a week
        self.skills_analyzer = SkillsAnalyzer()  # Initialize skills analyzer
        
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
        
        # Headers to avoid bot detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }

    def validate_url(self, url):
        """Validate if the URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            logger.error(f"URL validation failed: {e}")
            return False

    def get_user_input(self):
        """Get job posting URL from user via popup window"""
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        while True:
            url = simpledialog.askstring(
                "Job Posting Date Checker",
                "Enter the job posting URL (or click Cancel to exit):",
                initialvalue="https://"
            )
            
            if url is None:  # User clicked Cancel
                root.destroy()
                return None
            
            if url.strip():  # User entered something
                root.destroy()
                return url.strip()
            
            # If empty string, show error and ask again
            messagebox.showerror("Invalid Input", "Please enter a valid URL or click Cancel to exit.")
        
        root.destroy()
        return None

    def fetch_page_content(self, url):
        """Fetch the content of the job posting page"""
        try:
            logger.info(f"Fetching content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched page content. Status code: {response.status_code}")
            return response.content.decode('utf-8', errors='ignore')
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Connection error occurred")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching page: {e}")
            return None

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

    def should_apply(self, days_since_posted):
        """Determine if user should apply based on posting age"""
        if days_since_posted is None:
            return None, "Could not determine posting date"
        
        if days_since_posted < 0:
            return True, f"Job posting is from the future ({abs(days_since_posted)} days ahead) - likely a fresh posting!"
        elif days_since_posted <= self.max_age_days:
            return True, f"✅ APPLY! Job is fresh ({days_since_posted} days old)"
        else:
            return False, f"❌ Don't apply. Job is too old ({days_since_posted} days old, max recommended: {self.max_age_days} days)"

    def display_results(self, url, date_info, parsed_date, days_since_posted, should_apply_result, content=None):
        """Display results to user"""
        recommendation, reason = should_apply_result
        
        # Analyze skills if content is provided
        skills_analysis = None
        if content and date_info:
            try:
                skills_analysis = self.skills_analyzer.analyze_job_posting(
                    url, content, date_info['date']
                )
            except Exception as e:
                logger.warning(f"Skills analysis failed: {e}")
        
        result_message = f"""
Job Posting Analysis Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 URL: {url}

📅 Date Found: {date_info['date'] if date_info else 'Not found'}
📍 Source: {date_info['source'] if date_info else 'N/A'}
🗓️ Parsed Date: {parsed_date if parsed_date else 'Could not parse'}
⏰ Days Since Posted: {days_since_posted if days_since_posted is not None else 'Unknown'}

🎯 RECOMMENDATION: {reason}"""

        # Add skills analysis to results
        if skills_analysis:
            result_message += f"""

🔧 SKILLS ANALYSIS:
Company: {skills_analysis['company']}
Position: {skills_analysis['job_title']}
Technical Skills Found: {skills_analysis['skills_found']}
Total Skill Mentions: {skills_analysis['total_mentions']}

Top Skills: {', '.join(skills_analysis['skills'][:10]) if skills_analysis['skills'] else 'None found'}"""
        
        print(result_message)
        logger.info(f"Analysis complete. Recommendation: {reason}")
        
        # Show popup with results and ask if user wants to check another URL
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Job Posting Analysis Results", result_message)
        
        # Ask about generating analytics
        if skills_analysis:
            show_analytics = messagebox.askyesno(
                "Generate Analytics?", 
                "Would you like to generate skills analytics charts from all analyzed jobs?"
            )
            if show_analytics:
                self.generate_and_show_analytics()
        
        # Ask if user wants to check another URL
        check_another = messagebox.askyesno(
            "Check Another URL?", 
            "Would you like to check another job posting URL?"
        )
        root.destroy()
        
        return check_another

    def generate_and_show_analytics(self):
        """Generate analytics and show results"""
        try:
            logger.info("Generating skills analytics...")
            analytics_result = self.skills_analyzer.generate_analytics()
            
            if analytics_result:
                # Show trending skills
                trending = self.skills_analyzer.get_trending_skills(15)
                
                trending_message = "📊 TOP TRENDING SKILLS:\n" + "━" * 30 + "\n"
                for i, skill in enumerate(trending[:10], 1):
                    trending_message += f"{i:2d}. {skill['skill_name']:15} | Jobs: {skill['total_jobs']:2d} | Mentions: {skill['total_occurrences']:3d}\n"
                
                trending_message += f"\n📈 Analytics saved to: analytics/\n"
                trending_message += f"📈 Total Jobs Analyzed: {analytics_result['total_jobs']}\n"
                trending_message += f"📈 Unique Companies: {analytics_result['unique_companies']}\n"
                trending_message += f"📈 Total Skills Tracked: {analytics_result['total_skills']}"
                
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Skills Analytics Generated!", trending_message)
                root.destroy()
                
                logger.info("Analytics generated and displayed successfully")
            else:
                root = tk.Tk()
                root.withdraw()
                messagebox.showwarning("Analytics Error", "Could not generate analytics. Please check the logs.")
                root.destroy()
                
        except Exception as e:
            logger.error(f"Error in generate_and_show_analytics: {e}")
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Analytics Error", f"Error generating analytics: {e}")
            root.destroy()

    def run(self):
        """Main execution function"""
        try:
            logger.info("Starting Job Posting Date Checker...")
            
            while True:  # Keep running until user chooses to exit
                # Get URL from user
                url = self.get_user_input()
                if not url:
                    logger.info("No URL provided by user or user cancelled. Exiting.")
                    break
                
                # Validate URL
                if not self.validate_url(url):
                    error_msg = "Invalid URL format. Please provide a valid HTTP/HTTPS URL."
                    logger.error(error_msg)
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showerror("Invalid URL", error_msg)
                    root.destroy()
                    continue  # Ask for another URL
                
                # Fetch page content
                content = self.fetch_page_content(url)
                if not content:
                    error_msg = "Failed to fetch page content. Please check the URL and try again."
                    logger.error(error_msg)
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showerror("Fetch Error", error_msg)
                    root.destroy()
                    continue  # Ask for another URL
                
                # Extract date information
                date_info = self.extract_date_from_content(content)
                if not date_info:
                    warning_msg = "Could not find posting date on this page. The job might be very new or the site format is not supported."
                    logger.warning(warning_msg)
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showwarning("Date Not Found", warning_msg)
                    check_another = messagebox.askyesno(
                        "Check Another URL?", 
                        "Would you like to try another job posting URL?"
                    )
                    root.destroy()
                    if not check_another:
                        break
                    continue  # Ask for another URL
                
                # Parse the date
                parsed_date = self.parse_date(date_info['date'])
                if not parsed_date:
                    error_msg = f"Found a date ({date_info['date']}) but could not parse it into a valid format."
                    logger.error(error_msg)
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showerror("Date Parse Error", error_msg)
                    check_another = messagebox.askyesno(
                        "Check Another URL?", 
                        "Would you like to try another job posting URL?"
                    )
                    root.destroy()
                    if not check_another:
                        break
                    continue  # Ask for another URL
                
                # Calculate days since posted
                days_since_posted = self.calculate_days_since_posted(parsed_date)
                
                # Make recommendation
                should_apply_result = self.should_apply(days_since_posted)
                
                # Display results and ask if user wants to check another URL
                check_another = self.display_results(url, date_info, parsed_date, days_since_posted, should_apply_result, content)
                
                if not check_another:
                    logger.info("User chose not to check another URL. Exiting.")
                    break
            
        except KeyboardInterrupt:
            logger.info("Process interrupted by user")
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            logger.error(error_msg)
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Unexpected Error", error_msg)
            root.destroy()

if __name__ == "__main__":
    checker = JobPostingDateChecker()
    checker.run()
