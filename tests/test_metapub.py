from pathlib import Path

import requests

# pubmedr.config must be imported before metapub to properly set NCBI_API_KEY
from pubmedr import config  # noqa: F401
from metapub import FindIt, PubMedFetcher


def download_article_pdfs(pmid_list, download_dir: Path):
    fetch = PubMedFetcher()
    download_dir.mkdir(parents=True, exist_ok=True)

    for pmid in pmid_list:
        article = fetch.article_by_pmid(pmid)
        finder = FindIt(pmid)

        url, reason = finder.load_from_cache(verify=True)
        print(f"\nProcessing {pmid}: {article.title}")

        if finder.url:
            try:
                response = requests.get(finder.url, timeout=30)
                if response.status_code == 200:
                    pdf_path = download_dir / f"{pmid}.pdf"
                    pdf_path.write_bytes(response.content)
                    print(f"✓ Downloaded PDF to {pdf_path}")
                else:
                    print(f"✗ Failed to download: HTTP {response.status_code}")
            except Exception as e:
                print(f"✗ Error downloading: {e}")
        else:
            print(f"✗ No PDF URL found. Reason: {finder.reason}")

        # Print fulltext if available
        if hasattr(article, "abstract"):
            print("\nAbstract:")
            # print(article.abstract)
        else:
            print("\nNo abstract available")


query = '("2024/11/01"[Date - Create] : "3000"[Date - Create]) AND (Wu[Author])'
fetch = PubMedFetcher()
pmids = fetch.pmids_for_query(query, retmax=9999)

print(f"pmids: {len(pmids)}")

download_article_pdfs(pmids[:20], Path("./data/dl_pdf"))
