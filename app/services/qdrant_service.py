import os
from qdrant_client import QdrantClient


def get_qdrant_client() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", "localhost")
    port_env = os.getenv("QDRANT_PORT", "6333")
    port = int(port_env) if port_env.isdigit() else 6333
    return QdrantClient(host=host, port=port)
