import logging
from .web_fetcher import WebFetcher
from .date_extractor import DateExtractor
from .recommendation_engine import RecommendationEngine
from .ui_manager import UIManager
from skills_analyzer import SkillsAnalyzer

logger = logging.getLogger(__name__)

class JobAnalyzer:
    """Main job analysis coordinator that orchestrates all components"""

    def __init__(self):
        self.web_fetcher = WebFetcher()
        self.date_extractor = DateExtractor()
        self.recommendation_engine = RecommendationEngine()
        self.ui_manager = UIManager()
        self.skills_analyzer = SkillsAnalyzer()

    def analyze_job_posting(self, url):
        """
        Analyze a single job posting URL
        
        Args:
            url (str): Job posting URL
            
        Returns:
            dict: Analysis results containing date info, recommendation, and skills
        """
        try:
            logger.info(f"Starting analysis of job posting: {url}")
            
            # Validate URL
            if not self.web_fetcher.validate_url(url):
                error_msg = f"Invalid URL format: {url}"
                logger.error(error_msg)
                return {"error": error_msg}
            
            # Fetch page content
            page_content = self.web_fetcher.fetch_page_content(url)
            if not page_content:
                error_msg = f"Failed to fetch content from: {url}"
                logger.error(error_msg)
                return {"error": error_msg}
            
            # Extract posting date
            date_info = self.date_extractor.find_posting_date(page_content, url)
            parsed_date = self.date_extractor.parse_date(date_info['date']) if date_info else None
            days_since_posted = self.date_extractor.calculate_days_since_posting(parsed_date) if parsed_date else None
            
            # Get application recommendation
            should_apply_result = self.recommendation_engine.should_apply_for_job(
                url, date_info, parsed_date, days_since_posted
            )
            
            # Perform skills analysis
            skills_analysis = None
            try:
                skills_analysis = self.skills_analyzer.analyze_job_posting(url, page_content['html'])
                logger.info(f"Skills analysis completed. Found {len(skills_analysis.get('skills', []))} skills")
            except Exception as e:
                logger.error(f"Skills analysis failed: {str(e)}")
            
            # Return comprehensive analysis results
            return {
                "url": url,
                "date_info": date_info,
                "parsed_date": parsed_date,
                "days_since_posted": days_since_posted,
                "should_apply_result": should_apply_result,
                "skills_analysis": skills_analysis,
                "priority_score": self.recommendation_engine.get_application_priority(days_since_posted),
                "urgency_level": self.recommendation_engine.get_urgency_level(days_since_posted)
            }
            
        except Exception as e:
            error_msg = f"Error analyzing job posting {url}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def run_interactive_analysis(self):
        """Run interactive job posting analysis with GUI"""
        logger.info("Starting interactive job posting analysis")
        
        try:
            while True:
                # Get URL from user
                url = self.ui_manager.get_user_input()
                if url is None:  # User cancelled
                    logger.info("User cancelled the analysis")
                    break
                
                # Analyze the job posting
                results = self.analyze_job_posting(url)
                
                # Handle errors
                if "error" in results:
                    self.ui_manager.show_error("Analysis Error", results["error"])
                    continue
                
                # Display results and get user choices
                check_another, show_analytics = self.ui_manager.display_results(
                    results["url"],
                    results["date_info"],
                    results["parsed_date"],
                    results["days_since_posted"],
                    results["should_apply_result"],
                    results["skills_analysis"]
                )
                
                # Generate analytics if requested
                if show_analytics:
                    try:
                        analytics_result = self.skills_analyzer.generate_analytics()
                        trending_skills = self.skills_analyzer.get_trending_skills(limit=10)
                        self.ui_manager.display_analytics_results(analytics_result, trending_skills)
                    except Exception as e:
                        logger.error(f"Failed to generate analytics: {str(e)}")
                        self.ui_manager.show_error("Analytics Error", f"Failed to generate analytics: {str(e)}")
                
                # Check if user wants to analyze another URL
                if not check_another:
                    logger.info("User chose not to check another URL")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Analysis interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in interactive analysis: {str(e)}")
            self.ui_manager.show_error("Unexpected Error", f"An unexpected error occurred: {str(e)}")
        
        logger.info("Interactive analysis session ended")

    def batch_analyze_urls(self, urls):
        """
        Analyze multiple job posting URLs in batch
        
        Args:
            urls (list): List of job posting URLs
            
        Returns:
            list: List of analysis results for each URL
        """
        logger.info(f"Starting batch analysis of {len(urls)} URLs")
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Analyzing URL {i}/{len(urls)}: {url}")
            result = self.analyze_job_posting(url)
            results.append(result)
        
        logger.info(f"Batch analysis completed. {len(results)} URLs processed")
        return results

    def get_analysis_summary(self, results_list):
        """
        Generate summary statistics from multiple analysis results
        
        Args:
            results_list (list): List of analysis results
            
        Returns:
            dict: Summary statistics
        """
        if not results_list:
            return {}
        
        valid_results = [r for r in results_list if "error" not in r]
        
        summary = {
            "total_analyzed": len(results_list),
            "successful_analyses": len(valid_results),
            "failed_analyses": len(results_list) - len(valid_results),
            "recommended_applications": len([r for r in valid_results if r["should_apply_result"][0]]),
            "average_posting_age": None,
            "most_common_skills": [],
            "priority_distribution": {}
        }
        
        if valid_results:
            # Calculate average posting age
            posting_ages = [r["days_since_posted"] for r in valid_results if r["days_since_posted"] is not None]
            if posting_ages:
                summary["average_posting_age"] = sum(posting_ages) / len(posting_ages)
            
            # Priority distribution
            priorities = [r["priority_score"] for r in valid_results]
            for priority in priorities:
                summary["priority_distribution"][priority] = summary["priority_distribution"].get(priority, 0) + 1
        
        return summary
