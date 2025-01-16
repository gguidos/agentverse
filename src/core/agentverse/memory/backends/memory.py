from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.core.agentverse.memory.backends.base import VectorStorageBackend

class InMemoryVectorStorage(VectorStorageBackend):
    """In-memory vector storage using numpy arrays"""
    
    def __init__(self):
        self.vectors = []
        self.texts = []
        self.metadata = []
        
    async def add_vectors(self, texts: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        self.texts.extend(texts)
        self.vectors.extend(vectors)
        self.metadata.extend(metadata)
        
    async def search_vectors(self, query_vector: List[float], limit: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        if not self.vectors:
            return []
            
        query_array = np.array(query_vector).reshape(1, -1)
        vectors_array = np.array(self.vectors)
        similarities = cosine_similarity(query_array, vectors_array)[0]
        
        # Apply filters
        filtered_indices = []
        for idx, meta in enumerate(self.metadata):
            if filter_dict is None or all(meta.get(k) == v for k, v in filter_dict.items()):
                filtered_indices.append(idx)
                
        if not filtered_indices:
            return []
            
        filtered_similarities = [(idx, similarities[idx]) for idx in filtered_indices]
        sorted_results = sorted(filtered_similarities, key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'text': self.texts[idx],
                'similarity': float(sim),
                'metadata': self.metadata[idx]
            }
            for idx, sim in sorted_results
        ]
        
    async def clear(self) -> None:
        self.vectors = []
        self.texts = []
        self.metadata = [] 