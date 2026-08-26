"""OmniAgent RAG Module Export

Alias module allowing clean imports via:
  from app.omniagent_rag import query_rag, OmniAgentRAG, get_rag_engine
"""

from app.rag_service import OmniAgentRAG, get_rag_engine, query_rag

__all__ = ["OmniAgentRAG", "get_rag_engine", "query_rag"]
