import tkinter as tk
from tkinter import messagebox, simpledialog
import logging

logger = logging.getLogger(__name__)

class UIManager:
    """Handles user interface interactions using tkinter"""

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

    def show_error(self, title, message):
        """Show error message to user"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()

    def show_warning(self, title, message):
        """Show warning message to user"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(title, message)
        root.destroy()

    def show_info(self, title, message):
        """Show info message to user"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()

    def ask_yes_no(self, title, message):
        """Ask user a yes/no question"""
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(title, message)
        root.destroy()
        return result

    def display_results(self, url, date_info, parsed_date, days_since_posted, 
                       should_apply_result, skills_analysis=None):
        """Display analysis results to user"""
        recommendation, reason = should_apply_result
        
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
        
        # Show popup with results
        self.show_info("Job Posting Analysis Results", result_message)
        
        # Ask about generating analytics if skills analysis was performed
        show_analytics = False
        if skills_analysis:
            show_analytics = self.ask_yes_no(
                "Generate Analytics?", 
                "Would you like to generate skills analytics charts from all analyzed jobs?"
            )
        
        # Ask if user wants to check another URL
        check_another = self.ask_yes_no(
            "Check Another URL?", 
            "Would you like to check another job posting URL?"
        )
        
        return check_another, show_analytics

    def display_analytics_results(self, analytics_result, trending_skills):
        """Display analytics results to user"""
        trending_message = "📊 TOP TRENDING SKILLS:\n" + "━" * 30 + "\n"
        for i, skill in enumerate(trending_skills[:10], 1):
            trending_message += f"{i:2d}. {skill['skill_name']:15} | Jobs: {skill['total_jobs']:2d} | Mentions: {skill['total_occurrences']:3d}\n"
        
        trending_message += f"\n📈 Analytics saved to: analytics/\n"
        trending_message += f"📈 Total Jobs Analyzed: {analytics_result['total_jobs']}\n"
        trending_message += f"📈 Unique Companies: {analytics_result['unique_companies']}\n"
        trending_message += f"📈 Total Skills Tracked: {analytics_result['total_skills']}"
        
        self.show_info("Skills Analytics Generated!", trending_message)
