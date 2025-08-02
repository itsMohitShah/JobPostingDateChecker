import requests
import regex
import datetime
import dateutil.parser as dparser

today = datetime.date.today()
# from bs4 import BeautifulSoup

url = "https://jobs.neura-robotics.com/offer/deep-learning-expert-human/7604f3cc-43e3-484b-9bdd-57af170f11f8" # 10.01.2025
# url = "https://job.deloitte.com/job-consultant-audit-mwd-_48965" # 25.07.2025


response = requests.get(url)


response_string = response.content.decode('utf-8')
# print("datePosted in search:", 'datePosted' in response_string)
for line in response_string.split('\n'):
    if 'datePosted' in line:
        # print("Found datePosted in line:", line.strip())
        # Extract the date using regex
        match = regex.search(r'"datePosted":\s*"([^"]+)"', line)
        if match:
            date_posted = match.group(1)
            print(f"Extracted Date Posted: {date_posted}")
            parsed_date = dparser.parse(date_posted, fuzzy=True)
            print(f"Parsed Date Posted: {parsed_date}")
            # how many days since posted
            days_since_posted = (today - parsed_date.date()).days
            print(f"Days since posted: {days_since_posted}")
            break
