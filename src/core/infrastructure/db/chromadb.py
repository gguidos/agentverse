from langchain.vectorstores.chroma import Chroma
from src.core.infrastructure.aws.get_embedings import GetEmbeddings
from langchain.schema.document import Document

class ChromaDB:
    def __init__(
            self,
            embeddings_client: GetEmbeddings,
            chroma_path: str
    ):
        embedding_function = embeddings_client.get_embedding_function()
        self.db = Chroma(
            persist_directory=chroma_path, 
            embedding_function=embedding_function
        )

    def add_documents(self, documents: list[Document], ids: list[str]):
        """Add documents to the ChromaDB."""
        self.db.add_documents(documents, ids=ids)
        self.db.persist()

    def get_documents(self, include: list = None):
        """Retrieve documents from the ChromaDB."""
        return self.db.get(include=include)

    def clear_collection(self, store_name: str):
        """Clear a specific collection in ChromaDB."""
        # Implement logic to clear the collection if needed
        pass