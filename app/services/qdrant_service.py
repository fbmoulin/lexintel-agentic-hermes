import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

# Single source for the default port. 6533 (not Qdrant's stock 6333) matches
# the repo posture everywhere else — .env.example, docker-compose.yml
# (QDRANT_HOST_PORT defaults to 6533) and the integration-test guard — and
# avoids colliding with a foreign Qdrant already bound to :6333.
DEFAULT_QDRANT_PORT = 6533


def is_qdrant_enabled() -> bool:
    return os.getenv("LEX_KRATOS_ENABLE_QDRANT", "false").lower() == "true"


def get_qdrant_client() -> "QdrantClient":
    """
    Create a QdrantClient using host and port values resolved from environment variables.

    Reads QDRANT_HOST (default "localhost") and QDRANT_PORT (default DEFAULT_QDRANT_PORT = 6533, the repo's compose/.env posture); if QDRANT_PORT contains only digits it is converted to an integer and used as the port, otherwise DEFAULT_QDRANT_PORT is used.

    Returns:
        QdrantClient: A QdrantClient configured with the resolved host and port.
    """
    if not is_qdrant_enabled():
        raise RuntimeError(
            "Qdrant real está desativado. Defina LEX_KRATOS_ENABLE_QDRANT=true "
            "somente em tarefa explícita de integração."
        )

    # Lazy import: the client is an optional extra (requirements-qdrant.txt),
    # not a dependency of the mocked v0.1 pipeline.
    from qdrant_client import QdrantClient

    host = os.getenv("QDRANT_HOST", "localhost")
    port_env = os.getenv("QDRANT_PORT", str(DEFAULT_QDRANT_PORT))
    port = int(port_env) if port_env.isdigit() else DEFAULT_QDRANT_PORT
    return QdrantClient(host=host, port=port)
