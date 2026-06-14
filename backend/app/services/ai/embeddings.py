import hashlib
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class EmbeddingsService:
    def __init__(self) -> None:
        self.api_key_configured = bool(settings.GEMINI_API_KEY) and HAS_GENAI
        self.dimension = 768  # Gemini standard embedding size

    def get_embedding(self, text: str) -> list[float]:
        if not self.api_key_configured:
            return self._mock_embedding(text)
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Gemini embedding generation error: {e}. Falling back to mock.")
            return self._mock_embedding(text)

    def _mock_embedding(self, text: str) -> list[float]:
        # Generate a deterministic pseudo-random float array based on the text hash
        hasher = hashlib.sha256(text.encode("utf-8"))
        digest = hasher.digest()
        
        # Build 768 float array using digest bytes repeated
        embedding = []
        for i in range(self.dimension):
            byte_val = digest[i % len(digest)]
            # Normalize to range [-1.0, 1.0]
            val = (byte_val / 127.5) - 1.0
            # Add some variability based on index
            val += (i / self.dimension) * 0.1
            embedding.append(val)
            
        return embedding

embeddings_service = EmbeddingsService()
