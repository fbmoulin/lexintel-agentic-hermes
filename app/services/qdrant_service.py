import os

from qdrant_client import QdrantClient


def is_qdrant_enabled() -> bool:
    return os.getenv("LEX_KRATOS_ENABLE_QDRANT", "false").lower() == "true"


def get_qdrant_client() -> QdrantClient:
    """
    Create a QdrantClient using host and port values resolved from environment variables.

    Reads QDRANT_HOST (default "localhost") and QDRANT_PORT (default "6333"); if QDRANT_PORT contains only digits it is converted to an integer and used as the port, otherwise port 6333 is used.

    Returns:
        QdrantClient: A QdrantClient configured with the resolved host and port.
    """
    if not is_qdrant_enabled():
        raise RuntimeError(
            "Qdrant real está desativado. Defina LEX_KRATOS_ENABLE_QDRANT=true "
            "somente em tarefa explícita de integração."
        )

    host = os.getenv("QDRANT_HOST", "localhost")
    port_env = os.getenv("QDRANT_PORT", "6333")
    port = int(port_env) if port_env.isdigit() else 6333
    return QdrantClient(host=host, port=port)
