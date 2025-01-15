from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

class SplitDocument:
    def __init__(self):
        pass
    
    def split_document(self, documents: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=80,
            length_function=len,
            is_separator_regex=False,
        )
        return text_splitter.split_documents(documents)