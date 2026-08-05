from fastapi import APIRouter, Request

from app.models import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
def query_rag(
    request: Request,
    payload: QueryRequest,
):
    return request.app.state.query_service.query(payload)
