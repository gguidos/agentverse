from infrastructure.db.chromadb import ChromaDB
from fastapi import Depends

def get_chromadb_client():
    return ChromaDB() 