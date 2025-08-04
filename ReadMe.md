# Job Posting Date Checker

A Python tool that extracts and analyzes job posting dates from URLs to help track how long job postings have been active.

## Features

✅ **Date Extraction**: Automatically detects posting dates from multiple sources:
- Meta tags (`datePosted`, `article:published_time`, etc.)
- JSON-LD structured data
- Text patterns in page content
- PDF creation dates for PDF job postings

✅ **Smart Recommendations**: Provides intelligent application advice based on posting age:
- 🚀 **DEFINITELY APPLY** - Fresh postings (≤7 days)
- ✅ **YES, APPLY** - Recent postings (≤30 days)  
- ⚠️ **APPLY SOON** - Older but viable postings (≤60 days)
- ❌ **DON'T APPLY** - Very old postings (>90 days)

✅ **Skills Analysis**: Tracks and analyzes technical skills mentioned in job descriptions:
- Detects 180+ technical skills (Python, JavaScript, AWS, Docker, etc.)
- Stores job data in SQLite database
- Generates analytics charts and trending skills reports
- Filters out JavaScript code to focus on actual job requirements

✅ **Interactive GUI**: User-friendly popup interface for easy URL input and results display

✅ **Comprehensive Logging**: Detailed logs for debugging and tracking analysis history

## How to Use main.py

### Prerequisites

1. **Install Python 3.6+** on your system
2. **Install required packages**:
   ```bash
   pip install requests python-dateutil beautifulsoup4 matplotlib seaborn pandas
   ```

### Running the Application

1. **Navigate to project directory**:
   ```bash
   cd d:\dev\Projects\JobPostingDateChecker
   ```

2. **Run the main script**:
   ```bash
   python main.py
   ```

### Step-by-Step Usage

1. **Launch Application**: Run `python main.py` in your terminal/command prompt

2. **Enter Job URL**: A popup window will appear asking for a job posting URL
   - Paste any job posting URL (Indeed, LinkedIn, company career pages, etc.)
   - Examples:
     - `https://www.indeed.com/viewjob?jk=12345`
     - `https://jobs.lever.co/company/job-id`
     - `https://company.com/careers/position`

3. **View Analysis Results**: The tool will display:
   - **Date Found**: When the job was posted
   - **Source**: Where the date was found (meta tag, JSON-LD, etc.)
   - **Days Since Posted**: How many days ago it was posted
   - **Recommendation**: Whether you should apply and why
   - **Skills Analysis**: Technical skills found and job details

4. **Optional Analytics**: Choose whether to generate skills analytics charts

5. **Continue or Exit**: Decide if you want to analyze another URL or exit

### Example Output

```
Job Posting Analysis Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 URL: https://example.com/job/123
📅 Date Found: 2025-08-01T10:30:00Z
📍 Source: meta tag (datePosted)
🗓️ Parsed Date: 2025-08-01
⏰ Days Since Posted: 3

🎯 RECOMMENDATION: 🚀 DEFINITELY APPLY - Very fresh posting! Only 3 days old!

🔧 SKILLS ANALYSIS:
Company: Tech Company Inc.
Position: Senior Python Developer
Technical Skills Found: ['Python', 'Django', 'PostgreSQL', 'AWS', 'Docker']
Total Skill Mentions: 12
```

### Advanced Features

#### Skills Analytics
- Automatically tracks all analyzed jobs in `jobs.db` SQLite database
- Generates charts showing trending skills across all analyzed positions
- Creates analytics reports in `analytics/` folder
- View historical data with `python view_analytics.py`

#### Logging
- All analysis activity is logged to `job_posting_checker.log`
- Includes detailed information about date extraction attempts
- Useful for debugging issues with specific websites

#### Supported Date Formats
- ISO 8601: `2025-08-04T10:30:00Z`
- Human readable: `August 4, 2025`
- Relative dates: `3 days ago`, `Posted yesterday`
- Various meta tag formats from job sites
- PDF creation dates for PDF job postings

### Troubleshooting

**No date found**: Some job sites don't include posting dates or use dynamic loading. The tool will still provide analysis based on available information.

**Skills not detected**: The tool filters out JavaScript code and focuses on actual job requirements. If legitimate skills aren't detected, they may be embedded in complex HTML structures.

**Connection errors**: Some sites block automated requests. The tool includes proper headers to minimize this issue.

**GUI not appearing**: Make sure you have tkinter installed (usually included with Python on Windows/Mac).

## Task Breakdown

### Core Functionality ✅ COMPLETED
- [x] Analyze job posting URL structure and response format
- [x] Extract structured data (JSON-LD) from HTML response
- [x] Parse and extract `datePosted` field from structured data
- [x] Handle alternative date field names (e.g., `publishedDate`, `createdDate`, `postingDate`)
- [x] Implement robust date parsing for multiple formats (ISO, relative dates, etc.)
- [x] Calculate days since posting date
- [x] Add error handling for missing or malformed dates
- [x] Add a pop up window to enter url
- [x] Parse meta tags for date information (`article:published_time`, `datePosted`, etc.)
- [x] Handle PDF job postings with creation date extraction
- [x] Provide intelligent application recommendations based on posting age

### Enhancement Tasks ✅ COMPLETED
- [x] Implement user-agent headers to avoid bot detection
- [x] Add logging for debugging failed extractions
- [x] Add comprehensive skills analysis and tracking
- [x] Store job data in SQLite database
- [x] Generate analytics charts and trending skills reports
- [x] Filter JavaScript noise from skills detection
- [x] Create persistent popup interface that doesn't auto-close
- [x] Add comprehensive error handling and user feedback

### Future Enhancements (Not Implemented)
- [ ] Add caching mechanism for repeated requests
- [ ] Explore WHOIS data extraction for domain analysis
- [ ] Parse domain creation and registration dates
- [ ] Compare job posting age vs domain age for context
- [ ] Add support for authentication-required job sites
- [ ] Implement batch processing for multiple URLs
- [ ] Add email notifications for fresh job postings
- [ ] Create web interface alternative to GUI