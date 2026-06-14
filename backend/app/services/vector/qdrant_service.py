import logging
from typing import Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Try importing Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import exceptions as qdrant_exceptions
    from qdrant_client.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

class QdrantService:
    def __init__(self) -> None:
        self.enabled = HAS_QDRANT
        self.client = None
        self.mock_store = {}  # Fallback in-memory collection store

        if self.enabled:
            try:
                # Setup timeout to fail fast if not running
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    timeout=3.0
                )
                # Test connection
                self.client.get_collections()
                logger.info("Successfully connected to Qdrant.")
                self._init_collections()
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant: {e}. Falling back to MOCK vector search.")
                self.client = None
        else:
            logger.warning("qdrant-client not installed. Running in MOCK vector search.")

    def _init_collections(self) -> None:
        if not self.client:
            return
        collections = ["resumes", "jobs", "questions"]
        for col in collections:
            try:
                self.client.get_collection(collection_name=col)
            except Exception:
                # Collection does not exist, create it
                try:
                    self.client.create_collection(
                        collection_name=col,
                        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                    )
                    logger.info(f"Created Qdrant collection: {col}")
                except Exception as create_err:
                    logger.error(f"Failed to create collection {col}: {create_err}")

    def upsert_vector(self, collection: str, entity_id: str, vector: list[float], payload: dict[str, Any]) -> None:
        # Save to mock store anyway for simple fallback verification
        if collection not in self.mock_store:
            self.mock_store[collection] = []
        self.mock_store[collection].append({
            "id": entity_id,
            "vector": vector,
            "payload": payload
        })

        if not self.client:
            return
        try:
            self.client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=entity_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Failed to upsert to Qdrant {collection}: {e}")

    def search_similar(self, collection: str, query_vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        if self.client:
            try:
                results = self.client.query_points(
                    collection_name=collection,
                    query=query_vector,
                    limit=limit
                )
                return [
                    {
                        "id": hit.id,
                        "score": hit.score,
                        "payload": hit.payload
                    }
                    for hit in results.points
                ]
            except Exception as e:
                logger.error(f"Qdrant search error in {collection}: {e}. Falling back to mock matching.")

        # Fallback basic list matching using dot product/cosine approximation in mock store
        hits = []
        col_store = self.mock_store.get(collection, [])
        for item in col_store:
            # Simple dot product
            score = sum(x * y for x, y in zip(query_vector, item["vector"]))
            # Normalize to 0-1 roughly
            norm_score = max(0.0, min(1.0, (score + 1.0) / 2.0))
            hits.append({
                "id": item["id"],
                "score": norm_score,
                "payload": item["payload"]
            })
        # Sort by score desc
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:limit]

qdrant_service = QdrantService()
