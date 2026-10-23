from dependency_injector import containers, providers
from scrapers.gma_rss_scraper import GMARssScraper
from scrapers.philstar_rss_scraper import PhilstarRssScraper
from scrapers.rappler_rss_scraper import RapplerRssScraper
from scrapers.gma_nation_webpage_scraper import GMANationArchiveWebPageScraper
from pipelines.news_ingestion_pipeline import NewsIngestionPipeline


class Container(containers.DeclarativeContainer):
    gma_rss_scraper = providers.Factory(GMARssScraper)
    philstar_rss_scraper = providers.Factory(PhilstarRssScraper)
    rappler_rss_scraper = providers.Factory(RapplerRssScraper)
    gma_nation_archive_webpage_scraper = providers.Factory(
        GMANationArchiveWebPageScraper
    )

    news_ingestion_pipeline = providers.Factory(
        NewsIngestionPipeline,
        gma_rss_scraper=gma_rss_scraper,
        philstar_rss_scraper=philstar_rss_scraper,
        rappler_rss_scraper=rappler_rss_scraper,
        gma_nation_archive_webpage_scraper=gma_nation_archive_webpage_scraper,
    )
