import asyncio
from datetime import datetime, timedelta, timezone
from scrapers.gma_rss_scraper import GMARssScraper
from scrapers.philstar_rss_scraper import PhilstarRssScraper
from scrapers.rappler_rss_scraper import RapplerRssScraper
from scrapers.gma_nation_webpage_scraper import GMANationArchiveWebPageScraper
from models.article import Article


class NewsIngestionPipeline:
    def __init__(
        self,
        gma_rss_scraper: GMARssScraper,
        philstar_rss_scraper: PhilstarRssScraper,
        rappler_rss_scraper: RapplerRssScraper,
        gma_nation_archive_webpage_scraper: GMANationArchiveWebPageScraper,
    ) -> None:
        self.__gma_rss_scraper = gma_rss_scraper
        self.__philstar_rss_scraper = philstar_rss_scraper
        self.__rappler_rss_scraper = rappler_rss_scraper
        self.__gma_nation_archive_webpage_scraper = gma_nation_archive_webpage_scraper

    async def execute(self) -> list[Article]:
        results = await asyncio.gather(
            *[
                self.__gma_rss_scraper.extract_articles(),
                self.__philstar_rss_scraper.extract_articles(),
                self.__rappler_rss_scraper.extract_articles(),
                self.__gma_nation_archive_webpage_scraper.scrape(),
            ]
        )

        articles = [
            article for scraper_articles in results for article in scraper_articles
        ]

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        recent_articles = [
            article
            for article in articles
            if (
                article.published_at is not None
                and article.published_at >= cutoff
                and article.content is not None
            )
        ]

        return recent_articles
