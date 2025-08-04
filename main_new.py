#!/usr/bin/env python3
"""
Job Posting Date Checker - Main Entry Point

A comprehensive tool for analyzing job postings, extracting posting dates,
providing application recommendations, and analyzing technical skills.

Features:
- Extract posting dates from various sources (meta tags, JSON-LD, text patterns)
- Provide intelligent application recommendations based on posting age
- Analyze and track technical skills mentioned in job descriptions
- Generate analytics and trending skills reports
- Interactive GUI interface for easy use

Usage:
    python main.py

Requirements:
    - Python 3.6+
    - See requirements.txt for package dependencies
"""

import logging
import sys
from utils import JobAnalyzer

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

def main():
    """Main entry point for the Job Posting Date Checker application"""
    try:
        logger.info("Starting Job Posting Date Checker application")
        
        # Initialize the job analyzer (orchestrates all components)
        analyzer = JobAnalyzer()
        
        # Run interactive analysis
        analyzer.run_interactive_analysis()
        
        logger.info("Job Posting Date Checker application ended")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in main application: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
