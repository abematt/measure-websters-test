from .basic_query import query_index
from .combined_query import query_combined
from .local_query import local_query
from .web_enrichment import web_enrichment

__all__ = [
    'query_index',
    'query_combined',
    'local_query',
    'web_enrichment'
]