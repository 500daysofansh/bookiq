"""
BookIQ Web Scraper
Uses Selenium + BeautifulSoup to scrape books from books.toscrape.com
books.toscrape.com is a legal, public site specifically built for scraping practice.

Features:
- Multi-page scraping with Selenium (headless Chrome)
- Fallback to requests + BeautifulSoup
- Smart detail page fetching for descriptions
- Graceful error handling & duplicate detection
"""
import time
import logging
import re
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com"
CATALOGUE_URL = f"{BASE_URL}/catalogue"


def _rating_word_to_num(word: str) -> float:
    return {'One': 1.0, 'Two': 2.0, 'Three': 3.0, 'Four': 4.0, 'Five': 5.0}.get(word, 0.0)


def _parse_book_listing(elem) -> Optional[Dict]:
    """Parse one book article element from listing page"""
    try:
        title_elem = elem.select_one('h3 a')
        if not title_elem:
            return None

        title = title_elem.get('title', title_elem.text).strip()

        # Build full URL from relative href
        href = title_elem.get('href', '')
        # href is like ../../catalogue/a-light-in-the-attic_1000/index.html
        # or ../a-light.../index.html depending on page depth
        slug = re.sub(r'^\.\./+(?:catalogue/)?', '', href)
        book_url = f"{CATALOGUE_URL}/{slug}"

        # Star rating (CSS class like "star-rating Three")
        rating_elem = elem.select_one('p.star-rating')
        rating = 0.0
        if rating_elem:
            for cls in rating_elem.get('class', []):
                rating = _rating_word_to_num(cls)
                if rating:
                    break

        price_elem = elem.select_one('p.price_color')
        price = price_elem.text.strip() if price_elem else 'N/A'

        avail_elem = elem.select_one('p.availability')
        availability = avail_elem.text.strip() if avail_elem else 'Unknown'

        img_elem = elem.select_one('div.thumbnail img, img.thumbnail')
        cover = ''
        if img_elem:
            src = img_elem.get('src', '')
            # src is like ../../media/cache/.../cover.jpg
            src = re.sub(r'^\.\./+', '', src)
            cover = f"{BASE_URL}/{src}"

        return {
            'title': title,
            'author': 'Unknown Author',
            'rating': rating,
            'num_reviews': 0,
            'price': price,
            'availability': availability,
            'book_url': book_url,
            'cover_image_url': cover,
            'description': '',
            'genre': '',
        }
    except Exception as e:
        logger.error(f"Error parsing listing element: {e}")
        return None


def _fetch_book_detail(book_url: str) -> Optional[Dict]:
    """Fetch description, genre and review count from individual book page"""
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        resp = requests.get(book_url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Description lives after the #product_description anchor
        desc_elem = soup.select_one('#product_description ~ p')
        description = desc_elem.text.strip() if desc_elem else ''

        # Genre = second-to-last breadcrumb item
        breadcrumbs = soup.select('ul.breadcrumb li a')
        genre = breadcrumbs[-1].text.strip() if breadcrumbs else ''

        # Number of reviews from product info table
        num_reviews = 0
        table = soup.select_one('table.table')
        if table:
            for row in table.select('tr'):
                th = row.select_one('th')
                td = row.select_one('td')
                if th and td and 'review' in th.text.lower():
                    try:
                        num_reviews = int(td.text.strip())
                    except ValueError:
                        pass

        return {'description': description, 'genre': genre, 'num_reviews': num_reviews}
    except Exception as e:
        logger.warning(f"Could not fetch detail for {book_url}: {e}")
        return None


def scrape_with_requests(max_pages: int = 5) -> List[Dict]:
    """
    Scrape books.toscrape.com using requests + BeautifulSoup.
    This is the primary scraper — fast and reliable.
    """
    books = []
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    for page_num in range(1, max_pages + 1):
        url = f"{BASE_URL}/catalogue/page-{page_num}.html"
        logger.info(f"[Scraper] Page {page_num}: {url}")

        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 404:
                logger.info(f"Page {page_num} not found — reached end of catalogue")
                break
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.select('article.product_pod')
            if not articles:
                logger.warning(f"No product articles on page {page_num}, stopping")
                break

            logger.info(f"  Found {len(articles)} books on page {page_num}")

            for article in articles:
                book = _parse_book_listing(article)
                if not book:
                    continue

                # Fetch richer detail from each book's own page
                detail = _fetch_book_detail(book['book_url'])
                if detail:
                    book.update(detail)

                books.append(book)
                logger.info(f"    ✓ {book['title'][:55]}")

            time.sleep(0.4)   # Polite crawl delay

        except requests.RequestException as e:
            logger.error(f"Request error on page {page_num}: {e}")
            break

    logger.info(f"[Scraper] Done — collected {len(books)} books")
    return books


def scrape_with_selenium(max_pages: int = 3) -> List[Dict]:
    """
    Selenium-based scraper (headless Chrome).
    Handles JavaScript-rendered content and more complex navigation.
    Falls back to requests scraper on any failure.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        logger.info("[Selenium] Launching headless Chrome …")
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        )

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 12)

        books = []

        for page_num in range(1, max_pages + 1):
            url = f"{BASE_URL}/catalogue/page-{page_num}.html"
            logger.info(f"[Selenium] Loading page {page_num}")
            driver.get(url)

            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article.product_pod')))
            except Exception:
                logger.warning(f"Timeout on page {page_num}")
                break

            time.sleep(0.8)   # Let any dynamic content settle
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            for article in soup.select('article.product_pod'):
                book = _parse_book_listing(article)
                if not book:
                    continue
                detail = _fetch_book_detail(book['book_url'])
                if detail:
                    book.update(detail)
                books.append(book)
                logger.info(f"  [Selenium] ✓ {book['title'][:55]}")

        driver.quit()
        logger.info(f"[Selenium] Done — {len(books)} books")
        return books

    except Exception as e:
        logger.warning(f"[Selenium] Failed ({e}), falling back to requests scraper")
        return scrape_with_requests(max_pages)


def scrape_books(max_pages: int = 5, use_selenium: bool = False) -> List[Dict]:
    """
    Main scraping entry point.
    use_selenium=True → Selenium (headless Chrome)
    use_selenium=False → requests + BeautifulSoup (default, faster)
    """
    if use_selenium:
        return scrape_with_selenium(max_pages)
    return scrape_with_requests(max_pages)
