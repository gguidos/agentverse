import hashlib
from typing import List
import logging

logger = logging.getLogger(__name__)

class CalculateChunkIds:
    """Calculate unique IDs for document chunks"""
    
    def calculate(self, chunks: List[str]) -> List[str]:
        """Calculate unique IDs for each chunk based on content hash"""
        try:
            chunk_ids = []
            for chunk in chunks:
                # Create SHA-256 hash of chunk content
                chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()
                chunk_ids.append(chunk_hash)
                
            logger.debug(f"Generated {len(chunk_ids)} chunk IDs")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error calculating chunk IDs: {str(e)}")
            raise