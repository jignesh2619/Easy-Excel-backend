"""
Embedding Service for Semantic Search

Generates vector embeddings for semantic similarity search.
Uses sentence-transformers for fast, local embeddings.
"""

import logging
from typing import List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Lazy loading to avoid import errors if not installed
_embedding_model = None

def get_embedding_model():
    """Get or initialize embedding model (lazy loading)"""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Using a lightweight, fast model
            # 'all-MiniLM-L6-v2' is fast and good for semantic search
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
            _embedding_model = None
    return _embedding_model


class EmbeddingService:
    """Service for generating and working with embeddings"""
    
    def __init__(self):
        """Initialize embedding service"""
        self.model = get_embedding_model()
        self.dimension = 384 if self.model else None  # all-MiniLM-L6-v2 dimension
    
    def is_available(self) -> bool:
        """Check if embedding service is available"""
        return self.model is not None
    
    def encode(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for a text
        
        Args:
            text: Text to encode
            
        Returns:
            Embedding vector or None if model not available
        """
        if not self.model:
            return None
        
        try:
            # Handle empty strings
            if not text or not text.strip():
                return None
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return None
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            return [None] * len(texts)
        
        try:
            # Filter out empty texts
            valid_texts = [t if t and t.strip() else "" for t in texts]
            embeddings = self.model.encode(valid_texts, batch_size=batch_size, convert_to_numpy=True)
            
            # Convert to list and handle None for empty texts
            result = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    result.append(embeddings[i])
                else:
                    result.append(None)
            
            return result
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            return [None] * len(texts)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score (0-1)
        """
        if vec1 is None or vec2 is None:
            return 0.0
        
        try:
            # Normalize vectors
            vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
            vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
            
            # Calculate cosine similarity
            similarity = np.dot(vec1_norm, vec2_norm)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        candidate_embeddings: List[Tuple[np.ndarray, any]], 
        top_k: int = 5
    ) -> List[Tuple[float, any]]:
        """
        Find most similar items to query
        
        Args:
            query_embedding: Query vector
            candidate_embeddings: List of (embedding, data) tuples
            top_k: Number of results to return
            
        Returns:
            List of (similarity_score, data) tuples, sorted by similarity
        """
        if query_embedding is None:
            return []
        
        similarities = []
        for candidate_emb, data in candidate_embeddings:
            if candidate_emb is not None:
                similarity = self.cosine_similarity(query_embedding, candidate_emb)
                similarities.append((similarity, data))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        return similarities[:top_k]

