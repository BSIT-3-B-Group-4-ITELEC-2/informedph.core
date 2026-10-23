import asyncio
import json
import re
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo
import httpx
import trafilatura
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from utils.clean_title import clean_title
from utils.clean_article_content import clean_article_content
from utils.normalize_date import normalize_date
from utils.canonicalize_url import canonicalize_url
from models.article import Article
from utils.url_string_converter import url_string_converter


class GMANationArchiveWebPageScraper:
    def __init__(self) -> None:
        self.__URL = "https://www.gmanetwork.com/news/archives/news-nation/"
        self.__ARTICLE_PATTERN = re.compile(r"^/news/topstories/nation/\d+/.+/story/?$")
        self.__PH_TIMEZONE = ZoneInfo("Asia/Manila")
        self.__MAX_CONCURRENT_DOWNLOADS = 10

    def __get_published_at(self, html_content: str) -> str | None:
        soup = BeautifulSoup(html_content, "html.parser")

        for script in soup.find_all(
            "script",
            attrs={"type": "application/ld+json"},
        ):
            raw_json = script.string or script.get_text()

            if not raw_json:
                continue

            try:
                data = json.loads(raw_json)
            except json.JSONDecodeError:
                continue

            objects = data if isinstance(data, list) else [data]

            while objects:
                obj = objects.pop(0)

                if not isinstance(obj, dict):
                    continue

                published_at = normalize_date(obj.get("datePublished"))

                if published_at:
                    return published_at

        return None

    def __process_article_html(self, html: str, url: str) -> dict | None:
        article_text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            output_format="txt",
            favor_precision=True,
            deduplicate=True,
        )

        if not article_text:
            return None

        return {
            "content": clean_article_content(article_text),
            "published_at": self.__get_published_at(html),
        }

    async def __extract_article(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        url: str,
    ) -> dict | None:
        if not url:
            return None

        try:
            # Only the network download occupies a semaphore slot.
            async with semaphore:
                response = await client.get(url)
                response.raise_for_status()

            # Extraction runs outside the event-loop thread.
            article = await asyncio.to_thread(
                self.__process_article_html,
                response.text,
                str(response.url),
            )

            if article is None:
                print(f"No article content extracted: {response.url}")
                return None

            return article

        except httpx.HTTPStatusError as error:
            if error.response.status_code == 403:
                print(f"Access forbidden (403): {url}")
            else:
                print(f"HTTP ERROR {error.response.status_code}: {url}")
            return None

        except httpx.HTTPError as error:
            print(f"DOWNLOAD ERROR: {url} - {error!r}")
            return None

        except Exception as error:
            print(f"EXTRACTION ERROR: {url} - {error!r}")
            return None

    async def __collect_article_urls(self, page) -> dict[str, str]:
        links = await page.locator("a[href]").evaluate_all("""
            elements => elements.map(a => ({
                url: a.href,
                title: a.innerText.trim()
            }))
        """)

        articles = {}

        for link in links:
            parsed = urlsplit(link["url"])

            if parsed.hostname != "www.gmanetwork.com":
                continue

            if not self.__ARTICLE_PATTERN.match(parsed.path):
                continue

            title = clean_title(link["title"])

            if not title:
                continue

            url = canonicalize_url(link["url"])
            articles[url] = title

        return articles

    async def __extract_articles(
        self,
        client,
        links: dict[str, str],
    ) -> list[Article]:
        semaphore = asyncio.Semaphore(self.__MAX_CONCURRENT_DOWNLOADS)

        results = await asyncio.gather(
            *[self.__extract_article(client, semaphore, url) for url in links]
        )

        articles: list[Article] = []

        for (url, title), article in zip(links.items(), results):
            if article is None:
                continue

            articles.append(
                Article(
                    title=title,
                    url=url_string_converter(url=url),
                    content=article["content"],
                    published_at=article["published_at"],
                )
            )

        return articles

    async def scrape(self) -> list[Article]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                page = await browser.new_page()

                await page.goto(
                    self.__URL,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                await page.wait_for_timeout(3000)

                all_article_urls = {}
                max_scrolls = 2

                for _ in range(max_scrolls):
                    current = await self.__collect_article_urls(page)
                    all_article_urls.update(current)

                    await page.evaluate("""
                        window.scrollTo(
                            0,
                            document.body.scrollHeight
                        )
                    """)

                    await page.wait_for_timeout(1500)

                all_article_urls.update(await self.__collect_article_urls(page))

                async with httpx.AsyncClient(
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/130.0.0.0 Safari/537.36"
                        )
                    },
                    timeout=30,
                    follow_redirects=True,
                ) as client:
                    results = await self.__extract_articles(
                        client,
                        all_article_urls,
                    )

                return results

            finally:
                await browser.close()
