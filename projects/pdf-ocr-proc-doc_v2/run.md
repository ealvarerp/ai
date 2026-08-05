Run the application
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edit .env with your Azure endpoints and credentials.
Then run:
```bash
uvicorn app.main:app --reload
```
OpenAPI docs:
```
http://localhost:8000/docs
```
Example API usage
Upload a PDF
```
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "file=@/path/to/document.pdf" \
  -F "source=web_upload"
```
Trigger Blob Storage sync
```
curl -X POST http://localhost:8000/api/ingest/sync/blob \
  -H "Content-Type: application/json" \
  -d '{
    "container": "pdf-documents",
    "prefix": "incoming/"
  }'
```
Query the RAG system
```
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the payment terms in the contract?",
    "top_k": 8
  }'
```

Production hardening checklist
1. For production, you should add:
- Managed Identity
- Use Azure Managed Identity instead of API keys where possible.
2. Retries
- Add tenacity retries around:
- Azure OpenAI calls
- Document Intelligence calls
- Search indexing
- Blob uploads
3. Background queue
- Replace FastAPI BackgroundTasks with:
 Azure Storage Queue
 Azure Service Bus
 Azure Functions
 Celery worker
4. OCR quality
Add actual image enhancement:
- Deskew
- Denoise
- Binarization
- DPI normalization
5. Chunking improvements
- Preserve headings.
- Use markdown structure from Document Intelligence.
- Chunk tables separately.
- Add parent-child chunking.
6. Citations
- Store page number.
- Store section title.
- Store bounding box coordinates.
- Return deep links to original PDF page.
7. Security
- Add authentication.
- Add RBAC.
- Add API keys or Microsoft Entra ID.
- Add content safety.
- Add PII redaction.
8. Observability
- Add OpenTelemetry.
- Add structured logging.
- Add metrics for:
- Ingestion success rate
- OCR confidence
- Retrieval latency
- LLM latency
- Cache hit rate


