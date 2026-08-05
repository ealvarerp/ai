```text
pdf-rag/
│
├── requirements.txt
├── .env.example
│
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── models.py
    │
    ├── security/
    │   ├── __init__.py
    │   └── credentials.py
    │
    ├── ingestion/
    │   ├── __init__.py
    │   └── connectors.py
    │
    ├── orchestration/
    │   ├── __init__.py
    │   └── pipeline.py
    │
    ├── preprocessing/
    │   ├── __init__.py
    │   └── pdf_ops.py
    │
    ├── document_intelligence/
    │   ├── __init__.py
    │   └── azure_di.py
    │
    ├── postprocessing/
    │   ├── __init__.py
    │   └── text_ops.py
    │
    ├── genai/
    │   ├── __init__.py
    │   ├── azure_openai.py
    │   ├── chunker.py
    │   └── enrichment.py
    │
    ├── storage/
    │   ├── __init__.py
    │   ├── blob_store.py
    │   ├── search_store.py
    │   ├── cosmos_store.py
    │   ├── sql_audit.py
    │   └── redis_cache.py
    │
    ├── query/
    │   ├── __init__.py
    │   ├── hybrid_search.py
    │   ├── content_safety.py
    │   ├── response_generator.py
    │   └── rag_pipeline.py
    │
    └── api/
        ├── __init__.py
        ├── routes_ingest.py
        └── routes_query.py
```
