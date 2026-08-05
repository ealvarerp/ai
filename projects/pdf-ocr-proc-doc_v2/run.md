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


