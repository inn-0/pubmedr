from pubmedr import config  # noqa: I001
from metapub import PubMedFetcher  # noqa: I001
# config must be imported before metapub

from pubmedr.data_models import S4Results

logger = config.custom_logger(__name__)


def fetch_pubmed_results(query: str, max_results: int = 15) -> list[S4Results]:
    """Fetch results from PubMed and convert to S4Results format."""
    if not query.strip():
        return []

    try:
        fetch = PubMedFetcher()
        pmids = fetch.pmids_for_query(query, retmax=max_results)

        results = []
        for pmid in pmids:
            try:
                article = fetch.article_by_pmid(pmid)
                results.append(S4Results.from_metapub_article(article))
            except Exception as e:
                logger.error(f"Error fetching PMID {pmid}: {e}")
                continue

        return results
    except Exception as e:
        if "Empty term and query_key" in str(e):
            return []
        raise


def fetch_multiple_queries(queries: list[str], max_results_per_query: int = 20) -> dict[str, list[S4Results]]:
    """Fetch results for multiple PubMed queries."""
    results = {}
    for query in queries:
        try:
            results[query] = fetch_pubmed_results(query, max_results_per_query)
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
            results[query] = []

    return results
