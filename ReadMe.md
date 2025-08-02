# Job Posting Date Checker

A Python tool that extracts and analyzes job posting dates from URLs to help track how long job postings have been active.

## Features

## Task Breakdown

### Core Functionality
- [ ] Analyze job posting URL structure and response format
- [ ] Extract structured data (JSON-LD) from HTML response
- [ ] Parse and extract `datePosted` field from structured data
- [ ] Handle alternative date field names (e.g., `publishedDate`, `createdDate`, `postingDate`)
- [ ] Implement robust date parsing for multiple formats (ISO, relative dates, etc.)
- [ ] Calculate days since posting date
- [ ] Add error handling for missing or malformed dates
- [ ] Add a pop up window to enter url
- [ ] Explore WHOIS data extraction for domain analysis
- [ ] Parse domain creation and registration dates
- [ ] Compare job posting age vs domain age for context

### Enhancement Tasks
- [ ] Implement user-agent headers to avoid bot detection
- [ ] Add logging for debugging failed extractions
- [ ] Add caching mechanism for repeated requests