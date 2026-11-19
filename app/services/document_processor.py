from pathlib import Path

import pymupdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def extract_documents(file_path: str | Path) -> list[Document]:
    """Extract text into LangChain documents, keeping PDF pages separate."""
    path = Path(file_path)
    file_extension = path.suffix.lower()

    if file_extension == ".pdf":
        documents = []
        with pymupdf.open(path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text("text").strip()
                if page_text:
                    documents.append(
                        Document(
                            page_content=page_text,
                            metadata={"source": path.name, "page": page_number},
                        )
                    )
        return documents

    if file_extension == ".txt":
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Latin-1 can decode legacy text files that are not valid UTF-8.
            text = path.read_text(encoding="latin-1")

        text = text.strip()
        if not text:
            return []

        return [Document(page_content=text, metadata={"source": path.name})]

    raise ValueError("Unsupported file type. Only PDF and TXT files are supported.")


def split_documents(documents: list[Document]) -> list[Document]:
    """Split extracted documents into overlapping text chunks."""
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def process_document(file_path: str | Path) -> list[Document]:
    """Extract and chunk a supported document file."""
    documents = extract_documents(file_path)
    return split_documents(documents)

