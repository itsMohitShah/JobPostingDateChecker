import re
import sqlite3
import logging
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class SkillsAnalyzer:
    def __init__(self, db_path='job_skills.db'):
        self.db_path = db_path
        self.init_database()
        
        # Comprehensive list of technical skills to search for
        self.technical_skills = {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin',
            'scala', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell', 'sql', 'html', 'css', 'dart', 'elixir',
            
            # Web Technologies
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'laravel', 'rails',
            'asp.net', 'blazor', 'next.js', 'nuxt.js', 'svelte', 'ember', 'backbone', 'jquery', 'bootstrap',
            'tailwind', 'sass', 'less', 'webpack', 'vite', 'parcel', 'rollup',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server', 'cassandra', 'dynamodb',
            'elasticsearch', 'neo4j', 'firebase', 'supabase', 'prisma', 'sequelize', 'mongoose',
            
            # Cloud Platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean', 'linode', 'vultr', 'vercel', 'netlify',
            's3', 'ec2', 'lambda', 'cloudformation', 'terraform', 'ansible', 'puppet', 'chef',
            
            # DevOps & Tools
            'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions', 'circleci', 'travis ci', 'bamboo',
            'git', 'svn', 'mercurial', 'nginx', 'apache', 'linux', 'ubuntu', 'centos', 'debian', 'windows server',
            
            # Data Science & AI
            'machine learning', 'deep learning', 'artificial intelligence', 'data science', 'big data', 'analytics',
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'opencv', 'nltk', 'spacy',
            'jupyter', 'apache spark', 'hadoop', 'kafka', 'airflow', 'dbt', 'snowflake', 'databricks',
            
            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'cordova', 'phonegap',
            
            # Testing
            'junit', 'pytest', 'jest', 'mocha', 'chai', 'selenium', 'cypress', 'puppeteer', 'playwright',
            'postman', 'newman', 'k6', 'jmeter',
            
            # Project Management & Methodologies
            'agile', 'scrum', 'kanban', 'waterfall', 'devops', 'ci/cd', 'tdd', 'bdd', 'microservices',
            'rest api', 'graphql', 'grpc', 'soap', 'oauth', 'jwt', 'saml',
            
            # Design & UI/UX
            'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator', 'ui/ux', 'user experience', 'user interface',
            
            # Business Intelligence
            'tableau', 'power bi', 'qlik', 'looker', 'grafana', 'kibana', 'splunk',
            
            # Other Technologies
            'blockchain', 'ethereum', 'solidity', 'web3', 'nft', 'cryptocurrency', 'iot', 'edge computing',
            'ar/vr', 'unity', 'unreal engine', 'blender', 'maya'
        }
        
        # Convert to lowercase for case-insensitive matching
        self.technical_skills = {skill.lower() for skill in self.technical_skills}

    def init_database(self):
        """Initialize SQLite database for storing skills data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_postings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    company TEXT,
                    job_title TEXT,
                    posting_date TEXT,
                    analyzed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_content TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    job_posting_id INTEGER,
                    occurrences INTEGER DEFAULT 1,
                    context TEXT,
                    FOREIGN KEY (job_posting_id) REFERENCES job_postings (id),
                    UNIQUE(skill_name, job_posting_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    total_occurrences INTEGER DEFAULT 0,
                    total_jobs INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(skill_name)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def extract_job_content(self, content, url):
        """Extract relevant job content from HTML"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside", 
                               "iframe", "noscript", "form", "input", "button"]):
                element.decompose()
            
            # Remove elements with common non-job-content classes/ids
            unwanted_selectors = [
                '[class*="navigation"]', '[class*="menu"]', '[class*="sidebar"]',
                '[class*="footer"]', '[class*="header"]', '[class*="cookie"]',
                '[class*="banner"]', '[class*="ad"]', '[class*="advertisement"]',
                '[id*="navigation"]', '[id*="menu"]', '[id*="sidebar"]',
                '[id*="footer"]', '[id*="header"]', '[class*="social"]'
            ]
            
            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Try to find job-specific content sections with priority order
            job_sections = []
            
            # High priority selectors - most specific to job content
            priority_selectors = [
                '[class*="job-description"]', '[id*="job-description"]',
                '[class*="job-content"]', '[id*="job-content"]',
                '[class*="position-description"]', '[class*="role-description"]',
                '[class*="job-details"]', '[id*="job-details"]',
                '[class*="requirements"]', '[id*="requirements"]',
                '[class*="qualifications"]', '[id*="qualifications"]',
                '[class*="responsibilities"]', '[id*="responsibilities"]'
            ]
            
            # Medium priority selectors
            medium_selectors = [
                'div[class*="job"]', 'section[class*="job"]', 'article[class*="job"]',
                'div[class*="position"]', 'div[class*="role"]',
                'div[class*="description"]', 'section[class*="description"]',
                'div[class*="content"]', 'section[class*="content"]',
                '.job-posting', '.job-listing', '.position-details'
            ]
            
            # Low priority selectors
            low_selectors = [
                'main', 'article', '[role="main"]', '.main-content',
                'div[class*="container"]', 'div[class*="wrapper"]'
            ]
            
            # Try selectors in priority order
            all_selectors = [priority_selectors, medium_selectors, low_selectors]
            
            for selector_group in all_selectors:
                if job_sections:  # If we found content, stop looking
                    break
                    
                for selector in selector_group:
                    elements = soup.select(selector)
                    for element in elements:
                        if element:
                            text = element.get_text(strip=True)
                            # Only include substantial text blocks (likely job content)
                            if text and len(text) > 100:  # At least 100 characters
                                # Check if it contains job-related keywords
                                text_lower = text.lower()
                                job_keywords = [
                                    'experience', 'requirements', 'responsibilities', 
                                    'qualifications', 'skills', 'education', 'years',
                                    'bachelor', 'master', 'degree', 'position', 'role',
                                    'candidate', 'applicant', 'we are looking', 'you will',
                                    'required', 'preferred', 'must have', 'should have'
                                ]
                                
                                if any(keyword in text_lower for keyword in job_keywords):
                                    job_sections.append(text)
                                    break  # Found good content, move to next selector
                
                if job_sections:  # If we found content in this priority level, stop
                    break
            
            # If still no specific job sections found, try body but filter more carefully
            if not job_sections:
                body = soup.find('body')
                if body:
                    # Get all text but filter out short snippets and common non-job content
                    all_text = body.get_text()
                    
                    # Split into paragraphs and filter
                    paragraphs = [p.strip() for p in all_text.split('\n') if p.strip()]
                    filtered_paragraphs = []
                    
                    for para in paragraphs:
                        # Skip very short text
                        if len(para) < 50:
                            continue
                        
                        # Skip common website elements
                        para_lower = para.lower()
                        skip_phrases = [
                            'cookie', 'privacy policy', 'terms of service',
                            'copyright', '© 20', 'all rights reserved',
                            'follow us', 'social media', 'newsletter',
                            'loading', 'please wait', 'javascript',
                            'browser', 'enable cookies', 'accept'
                        ]
                        
                        if any(phrase in para_lower for phrase in skip_phrases):
                            continue
                        
                        # Include if it looks like job content
                        job_indicators = [
                            'experience', 'requirements', 'responsibilities',
                            'qualifications', 'skills', 'position', 'role',
                            'candidate', 'years of experience', 'degree',
                            'we are looking', 'you will', 'required', 'preferred'
                        ]
                        
                        if any(indicator in para_lower for indicator in job_indicators):
                            filtered_paragraphs.append(para)
                    
                    if filtered_paragraphs:
                        job_sections = filtered_paragraphs
            
            # Join all sections and clean up
            if job_sections:
                job_text = ' '.join(job_sections)
            else:
                job_text = ''
            
            # Clean up text more thoroughly
            if job_text:
                # Remove extra whitespace
                job_text = re.sub(r'\s+', ' ', job_text)
                job_text = job_text.strip()
                
                # Remove very long single "words" (likely encoded data or URLs)
                words = job_text.split()
                filtered_words = []
                for word in words:
                    # Skip very long strings that are likely not real words
                    if len(word) > 50:
                        continue
                    # Skip strings that look like encoded data or hashes
                    if re.match(r'^[a-f0-9]{20,}$', word.lower()):
                        continue
                    filtered_words.append(word)
                
                job_text = ' '.join(filtered_words)
            
            # Try to extract company name and job title
            company = self.extract_company_name(soup, url)
            job_title = self.extract_job_title(soup)
            
            logger.info(f"Extracted job content: {len(job_text)} characters from {len(job_sections)} sections")
            return {
                'content': job_text,
                'company': company,
                'job_title': job_title
            }
            
        except Exception as e:
            logger.error(f"Error extracting job content: {e}")
            return {'content': '', 'company': '', 'job_title': ''}

    def extract_company_name(self, soup, url):
        """Try to extract company name from various sources"""
        try:
            # Try meta tags first
            company_selectors = [
                'meta[property="og:site_name"]',
                'meta[name="author"]',
                'meta[name="company"]',
                '[class*="company"]',
                '[class*="employer"]',
                'h1', 'title'
            ]
            
            for selector in company_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        content = element.get('content', '')
                    else:
                        content = element.get_text(strip=True)
                    
                    if content and len(content) < 100:  # Reasonable company name length
                        return content
            
            # Fallback: extract from URL
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain:
                # Remove www. and .com/.org etc.
                company = domain.replace('www.', '').split('.')[0]
                return company.title()
                
        except Exception as e:
            logger.debug(f"Error extracting company name: {e}")
        
        return "Unknown"

    def extract_job_title(self, soup):
        """Try to extract job title"""
        try:
            # Try various selectors for job title
            title_selectors = [
                'h1[class*="job"]', 'h1[class*="title"]', 'h1[class*="position"]',
                '.job-title', '.position-title', '.role-title',
                'meta[property="og:title"]', 'title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        title = element.get('content', '')
                    else:
                        title = element.get_text(strip=True)
                    
                    if title and len(title) < 200:  # Reasonable title length
                        return title
                        
        except Exception as e:
            logger.debug(f"Error extracting job title: {e}")
        
        return "Unknown Position"

    def extract_skills(self, job_content):
        """Extract technical skills from job content"""
        try:
            # Pre-filter content to remove obvious non-job text
            content_lines = job_content.split('\n')
            filtered_lines = []
            
            for line in content_lines:
                line = line.strip()
                if len(line) < 10:  # Skip very short lines
                    continue
                
                line_lower = line.lower()
                
                # Skip lines that are clearly not job content
                skip_patterns = [
                    r'^[a-f0-9]{20,}$',  # Long hex strings
                    r'function\s*\(',     # JavaScript functions
                    r'var\s+\w+\s*=',     # JavaScript variables
                    r'window\.',          # JavaScript window object
                    r'document\.',        # JavaScript document object
                    r'\.js$',             # JavaScript file references
                    r'\.css$',            # CSS file references
                    r'console\.log',      # Console logs
                    r'addEventListener',   # Event listeners
                    r'getElementById',     # DOM manipulation
                    r'innerHTML',         # DOM manipulation
                    r'className',         # DOM manipulation
                    r'loading\.\.\.+',    # Loading messages
                    r'please wait',       # Loading messages
                    r'privacy policy',    # Legal text
                    r'terms of service',  # Legal text
                    r'cookie policy',     # Legal text
                    r'©\s*20\d{2}',      # Copyright
                ]
                
                should_skip = False
                for pattern in skip_patterns:
                    if re.search(pattern, line_lower):
                        should_skip = True
                        break
                
                if not should_skip:
                    filtered_lines.append(line)
            
            filtered_content = ' '.join(filtered_lines)
            content_lower = filtered_content.lower()
            
            # Only proceed if we have substantial content
            if len(filtered_content) < 100:
                logger.warning("Filtered content too short, might be extracting wrong content")
                return {}
            
            found_skills = {}
            
            for skill in self.technical_skills:
                # Create more precise regex patterns
                patterns = []
                
                # Basic pattern with word boundaries
                patterns.append(rf'\b{re.escape(skill)}\b')
                
                # Add plural form for most skills
                if not skill.endswith('s'):
                    patterns.append(rf'\b{re.escape(skill)}s\b')
                
                # Special patterns for certain technologies
                if skill in ['react', 'vue', 'angular']:
                    patterns.append(rf'\b{re.escape(skill)}\.js\b')
                    patterns.append(rf'\b{re.escape(skill)}\s+js\b')
                
                if skill == 'c++':
                    patterns.extend([r'\bc\+\+\b', r'\bcplusplus\b'])
                elif skill == 'c#':
                    patterns.extend([r'\bc#\b', r'\bc-sharp\b', r'\bcsharp\b'])
                elif skill == 'node.js':
                    patterns.extend([r'\bnode\.js\b', r'\bnodejs\b', r'\bnode\s+js\b'])
                elif skill == 'asp.net':
                    patterns.extend([r'\basp\.net\b', r'\baspnet\b', r'\basp\s+net\b'])
                elif skill == 'next.js':
                    patterns.extend([r'\bnext\.js\b', r'\bnextjs\b', r'\bnext\s+js\b'])
                elif skill == 'vue':
                    patterns.extend([r'\bvue\.js\b', r'\bvuejs\b'])
                
                total_occurrences = 0
                contexts = []
                
                for pattern in patterns:
                    matches = list(re.finditer(pattern, content_lower, re.IGNORECASE))
                    
                    # Filter out matches that are part of URLs, file paths, or technical strings
                    valid_matches = []
                    for match in matches:
                        start_pos = max(0, match.start() - 10)
                        end_pos = min(len(content_lower), match.end() + 10)
                        surrounding = content_lower[start_pos:end_pos]
                        
                        # Skip if it's part of a URL, file path, or technical identifier
                        if any(indicator in surrounding for indicator in [
                            'http://', 'https://', 'www.', '.com', '.org', '.net',
                            'file://', '/', '\\', '.min.', '.bundle.', 
                            'import ', 'require(', 'from ', 'class=', 'id='
                        ]):
                            continue
                        
                        valid_matches.append(match)
                    
                    total_occurrences += len(valid_matches)
                    
                    # Extract context around valid matches
                    for match in valid_matches[:3]:  # Limit to first 3 matches
                        start = max(0, match.start() - 50)
                        end = min(len(filtered_content), match.end() + 50)
                        context = filtered_content[start:end].strip()
                        contexts.append(context)
                
                if total_occurrences > 0:
                    found_skills[skill] = {
                        'occurrences': total_occurrences,
                        'contexts': contexts
                    }
            
            logger.info(f"Found {len(found_skills)} technical skills in filtered content")
            
            # Log some found skills for debugging
            if found_skills:
                top_skills = sorted(found_skills.items(), key=lambda x: x[1]['occurrences'], reverse=True)[:10]
                skill_names = [skill for skill, _ in top_skills]
                logger.info(f"Top skills found: {', '.join(skill_names)}")
            
            return found_skills
            
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return {}

    def save_to_database(self, url, job_data, posting_date, skills_data):
        """Save job posting and skills data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update job posting
            cursor.execute('''
                INSERT OR REPLACE INTO job_postings 
                (url, company, job_title, posting_date, raw_content)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, job_data['company'], job_data['job_title'], 
                  posting_date, job_data['content']))
            
            job_posting_id = cursor.lastrowid
            
            # Insert skills
            for skill, data in skills_data.items():
                context = ' | '.join(data['contexts'][:2])  # Limit context size
                
                cursor.execute('''
                    INSERT OR REPLACE INTO skills 
                    (skill_name, job_posting_id, occurrences, context)
                    VALUES (?, ?, ?, ?)
                ''', (skill, job_posting_id, data['occurrences'], context))
                
                # Update skill trends
                cursor.execute('''
                    INSERT OR REPLACE INTO skill_trends (skill_name, total_occurrences, total_jobs)
                    VALUES (?, 
                        COALESCE((SELECT total_occurrences FROM skill_trends WHERE skill_name = ?), 0) + ?,
                        COALESCE((SELECT total_jobs FROM skill_trends WHERE skill_name = ?), 0) + 1)
                ''', (skill, skill, data['occurrences'], skill))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved job posting and {len(skills_data)} skills to database")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False

    def generate_analytics(self, output_dir='analytics'):
        """Generate analytical charts and reports"""
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            
            # Get skill trends data
            df_trends = pd.read_sql_query('''
                SELECT skill_name, total_occurrences, total_jobs, 
                       ROUND(CAST(total_occurrences AS FLOAT) / total_jobs, 2) as avg_per_job
                FROM skill_trends 
                ORDER BY total_occurrences DESC 
                LIMIT 30
            ''', conn)
            
            if df_trends.empty:
                logger.warning("No skills data found for analytics")
                return
            
            # Set up the plotting style
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # Create subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
            
            # 1. Top Skills by Total Occurrences
            top_20_skills = df_trends.head(20)
            bars1 = ax1.barh(range(len(top_20_skills)), top_20_skills['total_occurrences'])
            ax1.set_yticks(range(len(top_20_skills)))
            ax1.set_yticklabels(top_20_skills['skill_name'])
            ax1.set_xlabel('Total Occurrences')
            ax1.set_title('Top 20 Most Mentioned Technical Skills', fontsize=14, fontweight='bold')
            ax1.grid(axis='x', alpha=0.3)
            
            # Add value labels on bars
            for i, bar in enumerate(bars1):
                width = bar.get_width()
                ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                        f'{int(width)}', ha='left', va='center')
            
            # 2. Top Skills by Number of Jobs
            bars2 = ax2.barh(range(len(top_20_skills)), top_20_skills['total_jobs'])
            ax2.set_yticks(range(len(top_20_skills)))
            ax2.set_yticklabels(top_20_skills['skill_name'])
            ax2.set_xlabel('Number of Job Postings')
            ax2.set_title('Top 20 Skills by Job Frequency', fontsize=14, fontweight='bold')
            ax2.grid(axis='x', alpha=0.3)
            
            # Add value labels
            for i, bar in enumerate(bars2):
                width = bar.get_width()
                ax2.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                        f'{int(width)}', ha='left', va='center')
            
            # 3. Average Mentions per Job
            bars3 = ax3.barh(range(len(top_20_skills)), top_20_skills['avg_per_job'])
            ax3.set_yticks(range(len(top_20_skills)))
            ax3.set_yticklabels(top_20_skills['skill_name'])
            ax3.set_xlabel('Average Mentions per Job')
            ax3.set_title('Top 20 Skills by Average Mentions per Job', fontsize=14, fontweight='bold')
            ax3.grid(axis='x', alpha=0.3)
            
            # Add value labels
            for i, bar in enumerate(bars3):
                width = bar.get_width()
                ax3.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                        f'{width:.1f}', ha='left', va='center')
            
            # 4. Skills Distribution by Category
            categories = {
                'Programming Languages': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust'],
                'Web Technologies': ['react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring'],
                'Databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite'],
                'Cloud & DevOps': ['aws', 'azure', 'docker', 'kubernetes', 'jenkins'],
                'Data Science': ['machine learning', 'deep learning', 'pandas', 'tensorflow', 'pytorch']
            }
            
            category_counts = {}
            for category, skills in categories.items():
                total = df_trends[df_trends['skill_name'].isin(skills)]['total_occurrences'].sum()
                if total > 0:
                    category_counts[category] = total
            
            if category_counts:
                ax4.pie(category_counts.values(), labels=category_counts.keys(), autopct='%1.1f%%')
                ax4.set_title('Skills Distribution by Category', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/skills_analytics.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Generate summary report
            self.generate_summary_report(df_trends, output_dir)
            
            # Get job posting stats
            job_stats = pd.read_sql_query('''
                SELECT COUNT(*) as total_jobs,
                       COUNT(DISTINCT company) as unique_companies,
                       MIN(analyzed_date) as first_analysis,
                       MAX(analyzed_date) as latest_analysis
                FROM job_postings
            ''', conn)
            
            conn.close()
            
            logger.info(f"Analytics generated successfully in {output_dir}/")
            return {
                'charts_saved': f'{output_dir}/skills_analytics.png',
                'total_skills': len(df_trends),
                'total_jobs': job_stats.iloc[0]['total_jobs'],
                'unique_companies': job_stats.iloc[0]['unique_companies']
            }
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return None

    def generate_summary_report(self, df_trends, output_dir):
        """Generate a text summary report"""
        try:
            report_path = f'{output_dir}/skills_summary_report.txt'
            
            with open(report_path, 'w') as f:
                f.write("JOB SKILLS ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("TOP 15 MOST IN-DEMAND SKILLS:\n")
                f.write("-" * 30 + "\n")
                for i, row in df_trends.head(15).iterrows():
                    f.write(f"{i+1:2d}. {row['skill_name']:20} | "
                           f"Occurrences: {row['total_occurrences']:3d} | "
                           f"Jobs: {row['total_jobs']:3d} | "
                           f"Avg/Job: {row['avg_per_job']:4.1f}\n")
                
                f.write(f"\n\nTOTAL UNIQUE SKILLS TRACKED: {len(df_trends)}\n")
                f.write(f"TOTAL SKILL MENTIONS: {df_trends['total_occurrences'].sum()}\n")
                f.write(f"TOTAL JOBS ANALYZED: {df_trends['total_jobs'].max()}\n")
                
            logger.info(f"Summary report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")

    def analyze_job_posting(self, url, content, posting_date):
        """Main method to analyze a job posting"""
        try:
            logger.info(f"Starting skills analysis for: {url}")
            
            # Extract job content
            job_data = self.extract_job_content(content, url)
            
            if not job_data['content']:
                logger.warning("No job content extracted")
                return None
            
            # Extract skills
            skills_data = self.extract_skills(job_data['content'])
            
            if not skills_data:
                logger.warning("No technical skills found")
                return None
            
            # Save to database
            success = self.save_to_database(url, job_data, posting_date, skills_data)
            
            if success:
                result = {
                    'url': url,
                    'company': job_data['company'],
                    'job_title': job_data['job_title'],
                    'skills_found': len(skills_data),
                    'skills': list(skills_data.keys()),
                    'total_mentions': sum(data['occurrences'] for data in skills_data.values())
                }
                
                logger.info(f"Skills analysis completed: {result['skills_found']} skills found")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing job posting: {e}")
            return None

    def get_trending_skills(self, limit=10):
        """Get currently trending skills"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT skill_name, total_occurrences, total_jobs
                FROM skill_trends 
                ORDER BY total_occurrences DESC 
                LIMIT ?
            ''', conn, params=[limit])
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting trending skills: {e}")
            return []
