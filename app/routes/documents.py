from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from langchain_chroma import Chroma

from app.database.vector_store import CHROMA_DB_DIR, COLLECTION_NAME, add_documents
from app.services.document_processor import process_document


router = APIRouter()
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _remove_new_upload(file_path: Path) -> None:
    """Remove only the file created by the current request, if it exists."""
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass


def _remove_new_chunks(source_filename: str) -> None:
    """Roll back chunks for this request if storage did not finish cleanly."""
    try:
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=str(CHROMA_DB_DIR),
        )
        vector_store.delete(where={"source": source_filename})
    except Exception:
        # Keep the original storage error as the response to the client.
        pass


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, str | int]:
    """Save, process, and store an uploaded PDF or TXT document."""
    original_filename = file.filename
    if not original_filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    file_extension = Path(original_filename).suffix.lower()
    if file_extension not in {".pdf", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are allowed.",
        )

    saved_filename = f"{uuid4().hex}{file_extension}"
    saved_path = DATA_DIR / saved_filename

    try:
        file_contents = await file.read()
        if not file_contents:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        saved_path.write_bytes(file_contents)
    except HTTPException:
        raise
    except Exception:
        _remove_new_upload(saved_path)
        raise HTTPException(
            status_code=500,
            detail="Unable to save the uploaded file.",
        ) from None

    try:
        chunks = process_document(saved_path)
    except Exception:
        _remove_new_upload(saved_path)
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be processed.",
        ) from None

    if not chunks:
        _remove_new_upload(saved_path)
        raise HTTPException(
            status_code=400,
            detail="No extractable text was found in the uploaded file.",
        )

    try:
        stored_ids = add_documents(chunks)
    except Exception:
        _remove_new_chunks(saved_filename)
        _remove_new_upload(saved_path)
        raise HTTPException(
            status_code=500,
            detail="Unable to store the processed document chunks.",
        ) from None

    return {
        "status": "success",
        "message": "File uploaded, processed, and stored successfully.",
        "original_filename": original_filename,
        "saved_filename": saved_filename,
        "chunks_processed": len(chunks),
        "chunks_stored": len(stored_ids),
    }
