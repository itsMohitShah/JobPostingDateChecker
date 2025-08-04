import requests
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WebFetcher:
    """Handles web requests and content fetching"""
    
    def __init__(self):
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
