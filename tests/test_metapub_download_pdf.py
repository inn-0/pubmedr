from pubmedr import config  # noqa: I001
from metapub import FindIt, PubMedFetcher  # noqa: I001

from pathlib import Path

import requests

# pubmedr.config must be imported before metapub to properly set NCBI_API_KEY


logger = config.custom_logger(__name__)


def download_article_pdfs(pmid_list, download_dir: Path):
    fetch = PubMedFetcher()
    download_dir.mkdir(parents=True, exist_ok=True)

    for pmid in pmid_list:
        article = fetch.article_by_pmid(pmid)
        finder = FindIt(pmid)

        url, reason = finder.load_from_cache(verify=True)
        logger.info(f"\nProcessing {pmid}: {article.title}")

        if finder.url:
            try:
                response = requests.get(finder.url, timeout=30)
                if response.status_code == 200:
                    pdf_path = download_dir / f"{pmid}.pdf"
                    pdf_path.write_bytes(response.content)
                    logger.info(f"✓ Downloaded PDF to {pdf_path}")
                else:
                    logger.error(f"✗ Failed to download: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"✗ Error downloading: {e}")
        else:
            logger.error(f"✗ No PDF URL found. Reason: {finder.reason}")

        if hasattr(article, "abstract"):
            logger.info("\nAbstract:")
        else:
            logger.info("\nNo abstract available")


query = '("2024/11/01"[Date - Create] : "3000"[Date - Create]) AND (Wu[Author])'
fetch = PubMedFetcher()
pmids = fetch.pmids_for_query(query, retmax=9999)

logger.info(f"pmids: {len(pmids)}")

download_article_pdfs(pmids[:20], Path("./data/dl_pdf"))
