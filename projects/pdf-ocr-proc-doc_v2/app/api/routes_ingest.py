import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile
from pydantic import BaseModel

from app.ingestion.connectors import BlobIngestionConnector

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


class BlobSyncRequest(BaseModel):
    container: str | None = None
    prefix: str | None = None


@router.post("/upload")
async def upload_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source: str = Form("web_upload"),
    password: str | None = Form(None),
):
    content = await file.read()
    document_id = str(uuid.uuid4())

    background_tasks.add_task(
        request.app.state.pipeline.process_pdf,
        file.filename or f"{document_id}.pdf",
        content,
        source,
        password,
        document_id,
    )

    return {
        "document_id": document_id,
        "status": "accepted",
    }


@router.post("/sync/blob")
def sync_blob_documents(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: BlobSyncRequest,
):
    settings = request.app.state.settings
    connector = BlobIngestionConnector(settings)

    accepted = 0

    for document in connector.fetch_documents(
        container=payload.container,
        prefix=payload.prefix,
    ):
        document_id = str(uuid.uuid4())

        background_tasks.add_task(
            request.app.state.pipeline.process_pdf,
            document.name,
            document.content,
            document.source,
            None,
            document_id,
        )

        accepted += 1

    return {
        "accepted_documents": accepted,
    }
