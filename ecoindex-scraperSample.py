import asyncio
from pprint import pprint

from ecoindex_scraper.scrap import EcoindexScraper

pprint(
    asyncio.run(
        EcoindexScraper(url="http://ecoindex.fr")
        .init_chromedriver()
        .get_page_analysis()
    )
)
