#!/usr/bin/env python3
"""
Standalone Skills Analytics Viewer
Run this script to generate analytics from the stored job skills data
"""

import sys
import os
import logging
from skills_analyzer import SkillsAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to generate analytics"""
    try:
        print("🔍 Job Skills Analytics Generator")
        print("=" * 50)
        
        # Initialize analyzer
        analyzer = SkillsAnalyzer()
        
        # Check if database exists
        if not os.path.exists(analyzer.db_path):
            print("❌ No database found. Please analyze some job postings first.")
            return
        
        # Generate analytics
        print("📊 Generating analytics...")
        result = analyzer.generate_analytics()
        
        if result:
            print("✅ Analytics generated successfully!")
            print(f"📈 Charts saved to: {result['charts_saved']}")
            print(f"📊 Total skills tracked: {result['total_skills']}")
            print(f"💼 Total jobs analyzed: {result['total_jobs']}")
            print(f"🏢 Unique companies: {result['unique_companies']}")
            
            # Show trending skills
            print("\n🔥 TOP 15 TRENDING SKILLS:")
            print("-" * 40)
            trending = analyzer.get_trending_skills(15)
            for i, skill in enumerate(trending, 1):
                print(f"{i:2d}. {skill['skill_name']:20} | "
                      f"Jobs: {skill['total_jobs']:3d} | "
                      f"Mentions: {skill['total_occurrences']:4d}")
            
            print(f"\n📁 Full report available in: analytics/skills_summary_report.txt")
            
        else:
            print("❌ Failed to generate analytics. Check logs for details.")
    
    except KeyboardInterrupt:
        print("\n⏹️ Analysis cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
