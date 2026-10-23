import asyncio
import feedparser
import httpx
import trafilatura
from utils.normalize_date import normalize_date
from utils.clean_text import clean_text
from models.article import Article
import asyncio
import feedparser
import httpx
import trafilatura
from utils.normalize_date import normalize_date
from utils.clean_text import clean_text
from models.article import Article


class PhilstarRssScraper:
    def __init__(self) -> None:
        self.__RSS_URL_LIST = [
            "https://www.philstar.com/rss/headlines",
            "https://www.philstar.com/rss/opinion",
            "https://www.philstar.com/rss/business",
            "https://www.philstar.com/rss/pilipino-star-ngayon/bansa",
            "https://interaksyon.philstar.com/politics-issues/feed/",
        ]

        self.__MAX_CONCURRENT_REQUESTS = 5

    async def __fetch_feed(self, client, url, semaphore) -> list[dict] | list:
        try:
            async with semaphore:
                response = await client.get(url)
                response.raise_for_status()

                feed = await asyncio.to_thread(
                    feedparser.parse,
                    url,
                )

            return [
                {
                    "title": clean_text(entry.get("title")),
                    "url": entry.get("link"),
                    "published_at": normalize_date(entry.get("published")),
                }
                for entry in feed.entries
                if entry.get("link")
            ]

        except (httpx.HTTPError, Exception) as error:
            print(f"RSS feed with URL-[{url}] cause error: {error}")
            return []

    async def __extract_article(self, client, url, semaphore) -> str | None:
        if not url:
            return None

        try:
            async with semaphore:
                response = await client.get(url)

            if response.status_code == 403:
                print(f"Access forbidden (403) with URL: {url}")
                return None

            response.raise_for_status()

        except httpx.HTTPError as error:
            print(f"Downloading Article with URL-[{url}] has failed: {error}")
            return None

        try:
            content = await asyncio.to_thread(
                trafilatura.extract,
                response.text,
                url=str(response.url),
                include_comments=False,
                include_tables=False,
                output_format="txt",
                favor_precision=True,
                deduplicate=True,
            )

            return content

        except Exception as error:
            print(f"Extracting Article with URL-[{url} has failed]: {error}")
            return None

    async def extract_articles(self) -> list[Article]:
        semaphore = asyncio.Semaphore(self.__MAX_CONCURRENT_REQUESTS)

        timeout = httpx.Timeout(30.0)

        async with httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/130.0.0.0 Safari/537.36"
                )
            },
            timeout=timeout,
            follow_redirects=True,
        ) as client:

            feed_results = await asyncio.gather(
                *[
                    self.__fetch_feed(client, url, semaphore)
                    for url in self.__RSS_URL_LIST
                ]
            )

            feed_entries = [entry for entries in feed_results for entry in entries]

            content_results = await asyncio.gather(
                *[
                    self.__extract_article(
                        client,
                        entry["url"],
                        semaphore,
                    )
                    for entry in feed_entries
                ]
            )

            articles = []
            for entry, content in zip(feed_entries, content_results):
                article = Article(
                    title=entry["title"],
                    url=entry["url"],
                    content=content,
                    published_at=entry["published_at"],
                )

                articles.append(article)

            return articles
