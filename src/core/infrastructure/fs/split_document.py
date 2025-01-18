from typing import List
import logging

logger = logging.getLogger(__name__)

class SplitDocument:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document splitter with configurable chunk size and overlap"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.debug(f"Initialized document splitter with chunk_size={chunk_size}, overlap={chunk_overlap}")

    async def split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        try:
            # Split text into words
            words = text.split()
            chunks = []
            
            # Calculate words per chunk (approximate characters to words)
            words_per_chunk = self.chunk_size // 5  # Assuming average word length of 5 chars
            overlap_words = self.chunk_overlap // 5
            
            # Create chunks with overlap
            i = 0
            while i < len(words):
                # Get chunk of words
                chunk_words = words[i:i + words_per_chunk]
                chunk = ' '.join(chunk_words)
                chunks.append(chunk)
                
                # Move index forward by chunk size minus overlap
                i += (words_per_chunk - overlap_words)
            
            logger.debug(f"Split text into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting document: {str(e)}")
            raise