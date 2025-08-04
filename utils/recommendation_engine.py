import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Handles job application recommendation logic"""

    def __init__(self):
        self.max_days_fresh = 30  # Jobs posted within 30 days are considered fresh
        self.max_days_recent = 60  # Jobs posted within 60 days are still worth applying to

    def should_apply_for_job(self, url, date_info, parsed_date, days_since_posted):
        """
        Determine if user should apply for the job based on posting date
        
        Returns:
            tuple: (should_apply: bool, reason: str)
        """
        try:
            if not date_info or not date_info['date']:
                logger.warning(f"No posting date found for {url}")
                return True, "❓ MAYBE APPLY - No posting date found. Could be a new listing!"
            
            if not parsed_date:
                logger.warning(f"Could not parse posting date: {date_info['date']}")
                return True, "❓ MAYBE APPLY - Found posting date but couldn't parse it. Check manually!"
            
            if days_since_posted is None:
                logger.warning(f"Could not calculate days since posting for {url}")
                return True, "❓ MAYBE APPLY - Could not determine posting age. Check manually!"
            
            # Decision logic based on days since posting
            if days_since_posted < 0:
                logger.info(f"Future posting date detected: {parsed_date}")
                return True, "🚀 DEFINITELY APPLY - Future posting date! This might be a premium listing!"
            
            elif days_since_posted <= 7:
                logger.info(f"Very fresh job posting: {days_since_posted} days old")
                return True, f"🚀 DEFINITELY APPLY - Very fresh posting! Only {days_since_posted} day{'s' if days_since_posted != 1 else ''} old!"
            
            elif days_since_posted <= self.max_days_fresh:
                logger.info(f"Fresh job posting: {days_since_posted} days old")
                return True, f"✅ YES, APPLY - Fresh posting! {days_since_posted} days old, good chance!"
            
            elif days_since_posted <= self.max_days_recent:
                logger.info(f"Recent job posting: {days_since_posted} days old")
                return True, f"⚠️ APPLY SOON - {days_since_posted} days old. Still worth applying but act fast!"
            
            elif days_since_posted <= 90:
                logger.info(f"Older job posting: {days_since_posted} days old")
                return False, f"⏰ MAYBE TOO LATE - {days_since_posted} days old. Position might be filled, but you could try."
            
            else:
                logger.info(f"Very old job posting: {days_since_posted} days old")
                return False, f"❌ DON'T APPLY - Very old posting ({days_since_posted} days). Likely filled or expired."
        
        except Exception as e:
            logger.error(f"Error in should_apply_for_job: {str(e)}")
            return True, f"❓ MAYBE APPLY - Error analyzing posting date: {str(e)}"

    def get_urgency_level(self, days_since_posted):
        """Get urgency level for job application"""
        if days_since_posted is None:
            return "unknown"
        elif days_since_posted < 0:
            return "premium"
        elif days_since_posted <= 7:
            return "urgent"
        elif days_since_posted <= 30:
            return "fresh"
        elif days_since_posted <= 60:
            return "recent"
        else:
            return "old"

    def get_application_priority(self, days_since_posted, skills_match_percentage=None):
        """
        Calculate application priority score (1-10, 10 being highest priority)
        
        Args:
            days_since_posted: Number of days since job was posted
            skills_match_percentage: Optional percentage of skill match (0-100)
        
        Returns:
            int: Priority score from 1-10
        """
        if days_since_posted is None:
            base_score = 5
        elif days_since_posted < 0:
            base_score = 10
        elif days_since_posted <= 7:
            base_score = 9
        elif days_since_posted <= 30:
            base_score = 7
        elif days_since_posted <= 60:
            base_score = 5
        elif days_since_posted <= 90:
            base_score = 3
        else:
            base_score = 1
        
        # Adjust score based on skills match if provided
        if skills_match_percentage is not None:
            if skills_match_percentage >= 80:
                base_score = min(10, base_score + 2)
            elif skills_match_percentage >= 60:
                base_score = min(10, base_score + 1)
            elif skills_match_percentage < 30:
                base_score = max(1, base_score - 1)
        
        return base_score
