"""
Agentic AI Landscape Tracker - Web Crawler
Fetches and processes content from AI news sources.
"""

import json
import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import feedparser
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dotenv import load_dotenv

from summarizer import Summarizer


class Crawler:
    """Main crawler class for fetching AI news from configured sources."""
    
    def __init__(self, config_path: str = "../config.yaml"):
        load_dotenv()
        self.config = self._load_config(config_path)
        self.summarizer = Summarizer()
        self.entries = []
        self.session = self._create_session()
        
    def _load_config(self, config_path: str) -> dict:
        """Load crawler configuration from YAML file, then overlay environment variables."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Overlay environment variables onto the loaded YAML config.
        # Any env var takes precedence over the YAML value.
        if os.getenv('CRAWLER_OUTPUT_PATH'):
            config.setdefault('output', {})['path'] = os.environ['CRAWLER_OUTPUT_PATH']

        crawler_section = config.setdefault('crawler', {})
        if os.getenv('CRAWLER_DELAY_BETWEEN_REQUESTS'):
            crawler_section['delay_between_requests'] = float(os.environ['CRAWLER_DELAY_BETWEEN_REQUESTS'])
        if os.getenv('CRAWLER_MAX_RETRIES'):
            crawler_section['max_retries'] = int(os.environ['CRAWLER_MAX_RETRIES'])
        if os.getenv('CRAWLER_TIMEOUT'):
            crawler_section['timeout'] = int(os.environ['CRAWLER_TIMEOUT'])

        backfill_section = config.setdefault('backfill', {})
        if os.getenv('CRAWLER_BACKFILL_ENABLED'):
            backfill_section['enabled'] = os.environ['CRAWLER_BACKFILL_ENABLED'].lower() in ('1', 'true', 'yes')
        if os.getenv('CRAWLER_BACKFILL_START_DATE'):
            backfill_section['start_date'] = os.environ['CRAWLER_BACKFILL_START_DATE']

        return config
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _generate_id(self, url: str, title: str) -> str:
        """Generate unique ID for an entry."""
        content = f"{url}{title}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text and clean up whitespace."""
        if not html_text:
            return ''
        
        # Parse HTML and extract text
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up excessive whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_article_content(self, article_elem) -> str:
        """Extract clean content from article element, excluding UI elements."""
        if not article_elem:
            return ''
        
        # Clone to avoid modifying original
        article = BeautifulSoup(str(article_elem), 'html.parser')
        
        # Remove common UI elements
        for selector in ['nav', 'button', '.button', 'footer', 'header', 
                        '.nav', '.navigation', '.menu', '.sidebar',
                        '.cookie', '.banner', '.ad', '.advertisement',
                        'script', 'style', 'iframe', 'noscript']:
            for elem in article.select(selector):
                elem.decompose()
        
        # Remove elements with common UI text patterns
        ui_text_patterns = [
            'learn more', 'read more', 'continue reading',
            'share', 'tweet', 'like', 'subscribe', 'follow',
            'previous', 'next', 'back', 'home',
            'your browser does not support the video tag',
            'your browser does not support',
            'models', 'research', 'announcements'
        ]
        
        # Collect elements to remove (don't remove during iteration)
        elements_to_remove = []
        for elem in article.find_all(string=True):
            text = elem.strip().lower()
            # Check if text contains any of the patterns
            for pattern in ui_text_patterns:
                if pattern in text or text == pattern:
                    parent = elem.parent
                    if parent and parent not in elements_to_remove:
                        elements_to_remove.append(parent)
                    break
        
        # Now remove collected elements
        for elem in elements_to_remove:
            elem.decompose()
        
        # Prioritize main content areas
        content = None
        for selector in ['article', 'main', '[role="main"]', '.content', 
                        '.article-content', '.post-content', '.entry-content',
                        'p']:
            elements = article.select(selector)
            if elements:
                # Get paragraphs for better content quality
                paragraphs = []
                for elem in elements:
                    if elem.name == 'p':
                        text = elem.get_text(strip=True)
                        if len(text) > 20:  # Only meaningful paragraphs
                            paragraphs.append(text)
                    else:
                        # Extract paragraphs from within the element
                        for p in elem.find_all('p'):
                            text = p.get_text(strip=True)
                            if len(text) > 20:
                                paragraphs.append(text)
                
                if paragraphs:
                    content = ' '.join(paragraphs[:5])  # First 5 paragraphs
                    break
        
        # Fallback to cleaned full text if no paragraphs found
        if not content:
            content = article.get_text(separator=' ', strip=True)
        
        # Clean up whitespace and limit length
        content = ' '.join(content.split())
        content = content[:800]  # Increased from 500 for better context
        
        # Remove common UI patterns from final content using regex
        import re
        ui_patterns = [
            r'january \d{4}',
            r'february \d{4}',
            r'march \d{4}',
            r'april \d{4}',
            r'may \d{4}',
            r'june \d{4}',
            r'july \d{4}',
            r'august \d{4}',
            r'september \d{4}',
            r'october \d{4}',
            r'november \d{4}',
            r'december \d{4}',
            r'learn more',
            r'read more',
            r'models',
            r'research',
            r'announcements',
            r'your browser does not support the video tag\.?'
        ]
        
        for pattern in ui_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Clean whitespace again after removals
        content = ' '.join(content.split())
        
        # Ensure it ends with proper punctuation
        if content and content[-1] not in '.!?':
            # Try to find last sentence ending
            for i in range(len(content)-1, max(len(content)-100, 0), -1):
                if content[i] in '.!?':
                    content = content[:i+1]
                    break
            else:
                content = content + '.'
        
        return content
    
    def _fetch_page(self, url: str, retry_count: int = 0, max_retries: int = None) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with retry logic for 403 errors."""
        if max_retries is None:
            max_retries = self.config.get('crawler', {}).get('max_retries', 3)
        
        try:
            # Enhanced headers to mimic real browser behavior
            # Note: Removed 'Accept-Encoding' to let requests handle compression automatically
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Add delay between requests to be respectful
            if retry_count > 0:
                delay = 2 ** retry_count  # Exponential backoff
                print(f"  Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                base_delay = self.config.get('crawler', {}).get('delay_between_requests', 1)
                time.sleep(base_delay)
            
            timeout = self.config.get('crawler', {}).get('timeout', 30)
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Ensure we get text content (handles decompression automatically)
            html_content = response.text
            return BeautifulSoup(html_content, 'html.parser')
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                if retry_count < max_retries:
                    print(f"  403 Forbidden on attempt {retry_count + 1}/{max_retries + 1}, retrying...")
                    return self._fetch_page(url, retry_count + 1, max_retries)
                else:
                    print(f"Error fetching {url}: 403 Forbidden - Site may require authentication or block automated access")
                    print(f"  Suggestion: Try using RSS feed or API if available")
            else:
                print(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _fetch_rss(self, rss_url: str) -> list:
        """Fetch and parse RSS feed."""
        try:
            feed = feedparser.parse(rss_url)
            entries = []
            for entry in feed.entries:
                # Get raw content and clean HTML tags
                raw_content = entry.get('summary', entry.get('description', ''))
                clean_content = self._clean_html(raw_content)
                
                # Apply same cleaning as article extraction
                if clean_content:
                    # Remove common UI patterns (case-insensitive)
                    ui_patterns = ['learn more', 'read more', 'continue reading',
                                 'share', 'tweet', 'subscribe', 'follow',
                                 'your browser does not support the video tag']
                    for pattern in ui_patterns:
                        # Case-insensitive replacement
                        import re
                        clean_content = re.sub(re.escape(pattern), '', clean_content, flags=re.IGNORECASE)
                    
                    # Clean whitespace
                    clean_content = ' '.join(clean_content.split())
                    
                    # Limit length and ensure proper ending
                    clean_content = clean_content[:800]
                    if clean_content and clean_content[-1] not in '.!?':
                        for i in range(len(clean_content)-1, max(len(clean_content)-100, 0), -1):
                            if clean_content[i] in '.!?':
                                clean_content = clean_content[:i+1]
                                break
                        else:
                            clean_content = clean_content + '.'
                
                entries.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'date': entry.get('published', entry.get('updated', '')),
                    'content': clean_content
                })
            return entries
        except Exception as e:
            print(f"Error fetching RSS {rss_url}: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format."""
        if not date_str:
            return None
        try:
            parsed = date_parser.parse(date_str)
            return parsed.strftime('%Y-%m-%d')
        except Exception:
            return None
    
    def _is_within_backfill_range(self, date_str: Optional[str]) -> bool:
        """Check if date is within backfill range."""
        if not date_str:
            return True  # Include if no date
        if not self.config.get('backfill', {}).get('enabled', False):
            return True
            
        start_date = self.config['backfill'].get('start_date', '2024-01-01')
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d')
            backfill_start = datetime.strptime(start_date, '%Y-%m-%d')
            return entry_date >= backfill_start
        except Exception:
            return True
    
    def crawl_source(self, source: dict) -> list:
        """Crawl a single source for articles."""
        # Skip disabled sources
        if not source.get('enabled', True):
            print(f"Skipping {source['name']} (disabled)")
            return []
        
        print(f"Crawling {source['name']}...")
        entries = []
        
        # Try RSS first if available
        if source.get('rss_url'):
            rss_entries = self._fetch_rss(source['rss_url'])
            for entry in rss_entries:
                date = self._parse_date(entry['date'])
                if not self._is_within_backfill_range(date):
                    continue
                    
                entries.append({
                    'id': self._generate_id(entry['url'], entry['title']),
                    'title': entry['title'],
                    'source': source['name'],
                    'url': entry['url'],
                    'date': date,
                    'content': entry['content'],
                    'summary': None,
                    'category': '',
                    'tags': []
                })
        else:
            # Fall back to HTML scraping
            soup = self._fetch_page(source['url'])
            if soup:
                selectors = source.get('selectors', {})
                articles = soup.select(selectors.get('article_list', 'article'))
                
                for article in articles[:20]:  # Limit to 20 per source
                    title_elem = article.select_one(selectors.get('title', 'h2'))
                    date_elem = article.select_one(selectors.get('date', 'time'))
                    
                    # Handle link: if selector is None/null, the article element itself is the link
                    link_selector = selectors.get('link', 'a')
                    if link_selector is None:
                        # Article element itself is the link
                        link_elem = article if article.name == 'a' else None
                    else:
                        link_elem = article.select_one(link_selector)
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '') if link_elem else ''
                    
                    # Handle relative URLs
                    if url and not url.startswith('http'):
                        from urllib.parse import urlparse
                        parsed = urlparse(source['url'])
                        
                        # If URL starts with '/', it's an absolute path from domain root
                        if url.startswith('/'):
                            url = f"{parsed.scheme}://{parsed.netloc}{url}"
                        else:
                            # Otherwise, it's relative to the source URL
                            base_url = source['url'].rstrip('/')
                            url = f"{base_url}/{url.lstrip('/')}"
                    
                    date_str = date_elem.get('datetime', date_elem.get_text(strip=True)) if date_elem else None
                    date = self._parse_date(date_str)
                    
                    if not self._is_within_backfill_range(date):
                        continue
                    
                    # Extract clean content
                    content = self._extract_article_content(article)
                    
                    entries.append({
                        'id': self._generate_id(url, title),
                        'title': title,
                        'source': source['name'],
                        'url': url,
                        'date': date,
                        'content': content,
                        'summary': None,
                        'category': '',
                        'tags': []
                    })
        
        print(f"  Found {len(entries)} entries from {source['name']}")
        return entries
    
    def crawl_all(self) -> list:
        """Crawl all configured sources."""
        all_entries = []
        
        for source in self.config.get('sources', []):
            entries = self.crawl_source(source)
            all_entries.extend(entries)
        
        # Remove duplicates by ID
        seen_ids = set()
        unique_entries = []
        for entry in all_entries:
            if entry['id'] not in seen_ids:
                seen_ids.add(entry['id'])
                unique_entries.append(entry)
        
        # Sort by date (newest first)
        unique_entries.sort(key=lambda x: x['date'] or '1900-01-01', reverse=True)
        
        return unique_entries
    
    def generate_summaries(self, entries: list) -> list:
        """Generate summaries and categorize entries using Copilot SDK."""
        print("Generating summaries and categories...")
        for entry in entries:
            if not entry.get('summary') and entry.get('content'):
                entry['summary'] = self.summarizer.summarize(
                    title=entry['title'],
                    content=entry['content'],
                    source=entry['source']
                )
            # Categorize entry (only if Copilot SDK available)
            if not entry.get('category') and entry.get('content'):
                entry['category'] = self.summarizer.categorize(
                    title=entry['title'],
                    content=entry['content']
                )
        return entries
    
    def save_entries(self, entries: list):
        """Save entries to JSON file."""
        output_path = Path(self.config['output']['path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'last_updated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'entries': entries
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(entries)} entries to {output_path}")
    
    def run(self):
        """Run the full crawl pipeline."""
        print("Starting crawler...")
        
        # Crawl all sources
        entries = self.crawl_all()
        
        # Generate summaries
        entries = self.generate_summaries(entries)
        
        # Save to file
        self.save_entries(entries)
        
        print("Crawl complete!")
        return entries


if __name__ == '__main__':
    from healthcheck import start_health_server
    start_health_server()
    crawler = Crawler()
    crawler.run()
