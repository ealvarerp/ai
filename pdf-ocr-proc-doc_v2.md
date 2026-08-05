<img width="1664" height="928" alt="azure ai foundry" src="https://github.com/user-attachments/assets/400aae6d-b464-433f-bd9e-03537f6799e2" />


# Enterprise PDF RAG Pipeline — Architecture Summary

> End-to-end Azure architecture for ingesting PDF documents, extracting content with OCR / Document Intelligence, enriching it with GenAI, indexing it for hybrid retrieval, and serving grounded answers across multiple channels.

---

## 1. Overview

The system is a 9-layer pipeline that turns unstructured PDFs into a searchable, AI-powered knowledge base:

1. **Ingestion** – collect PDFs from 5 source types
2. **Orchestration** – route work via Data Factory / Functions / Logic Apps
3. **PDF Pre-Processing** – validate, enhance, segment, decrypt
4. **OCR & Document Intelligence** – extract text, tables, figures, handwriting
5. **Post-Processing & Validation** – normalize, detect language, score confidence, human review, metadata
6. **Gen AI Processing** – chunk, embed, summarize, NER, classify
7. **Storage** – indexes, metadata, originals, audit logs, cache
8. **Query & Retrieval** – hybrid search + RAG with safety filtering
9. **Output & Integration** – API, Web UI, Power BI, Teams, exports

---

## 2. Layer-by-Layer Breakdown

### 📥 2.1 Ingestion Layer
| Component | Role | Routed To |
|---|---|---|
| SharePoint | Document libraries | Azure Data Factory |
| Azure Blob Storage | Bulk file landing zone | Azure Functions |
| Email Attachments | Mail-driven intake | Logic Apps |
| Web Upload | Manual user uploads | Azure Functions |
| FTP/SFTP | Legacy / partner transfers | Azure Data Factory |

### 🔄 2.2 Orchestration Layer
| Component | Role |
|---|---|
| Azure Data Factory | Batch / scheduled pipeline orchestration |
| Azure Functions | Event-driven triggers |
| Logic Apps | Workflow automation |

All three converge on **PDF Validation**, the single entry point into processing.

### 📄 2.3 PDF Pre-Processing (sequential)
1. **PDF Validation** – format check *(also archives the original PDF to Blob Storage)*
2. **Image Enhancement** – deskew / denoise for scanned pages
3. **Page Segmentation** – multi-page split for batch processing
4. **Password Removal** – decryption before OCR

### 🔍 2.4 OCR & Document Intelligence
**Azure AI Document Intelligence (layout analysis)** fans out to:
- **OCR Engine** – text recognition
- **Table Extraction** – structure detection
- **Figure/Chart Detection** – image analysis
- **Handwriting Recognition (ICR)**

All extraction outputs converge into **Text Normalization**.

### 🧹 2.5 Post-Processing & Validation (quality gate)
1. **Text Normalization** – Unicode cleanup
2. **Language Detection** – multi-language support
3. **Confidence Scoring** – quality metrics *(written to SQL audit logs)*
4. **Human-in-the-Loop** – validation queue for low-confidence documents
5. **Metadata Extraction** – author / date / tags

### 🧠 2.6 Gen AI Processing
**Semantic Chunking (500–1000 tokens)** fans out to parallel enrichment:
- **Embedding Generation** (Azure OpenAI) → Azure AI Search
- **Summarization** (GPT-4o) → Cosmos DB
- **Entity Extraction / NER** → Cosmos DB
- **Classification** (document type) → Cosmos DB

### 💾 2.7 Storage Layer
| Store | Contents |
|---|---|
| Azure AI Search | Vector + keyword (BM25) index |
| Cosmos DB | Document metadata, summaries, entities, classifications |
| Blob Storage | Original PDFs |
| SQL Database | Audit logs / quality metrics |
| Redis Cache | Frequent query results |

### 🔎 2.8 Query & Retrieval (sequential)
1. **Hybrid Search** – vector + BM25 over Azure AI Search
2. **RAG Pipeline** – context assembly
3. **Content Safety** – pre/post filtering
4. **Response Generation** – GPT-4o

### 📤 2.9 Output & Integration
| Channel | Fed By |
|---|---|
| REST API (FastAPI/Flask) | Response Generation |
| Web UI (React/Angular) | Response Generation |
| Power BI (Analytics Dashboard) | Cosmos DB metadata |
| Microsoft Teams (Bot) | Response Generation |
| Export Formats (JSON/CSV/Markdown) | Response Generation |

---

## 3. Data Flow

### 3.1 Write Path (Ingest → Index)
```text
Sources → Orchestrators → Validate → Enhance → Segment → Decrypt
→ Document Intelligence → (OCR | Tables | Figures | Handwriting)
→ Normalize → Language → Confidence → HITL → Metadata
→ Chunk → (Embed | Summarize | NER | Classify)
→ AI Search + Cosmos DB   (+ Blob originals, + SQL audit logs)
```

### 3.2 Read Path (Query → Answer)
```text
User Query → Hybrid Search (AI Search) → RAG Context Assembly
→ Content Safety → GPT-4o Generation → API / Web UI / Teams / Exports
```

---

## 4. Key Design Highlights

- **Source-appropriate orchestration** – batch sources use Data Factory, event sources use Functions, workflow sources use Logic Apps; all funnel into one processing pipeline.
- **Quality-first processing** – confidence scoring + human-in-the-loop review before indexing low-quality OCR output.
- **Purpose-built storage separation** – vectors in AI Search, metadata in Cosmos, immutable originals in Blob, audit trail in SQL, hot results in Redis.
- **Hybrid retrieval** – vector similarity + BM25 keyword ranking for robust recall.
- **Responsible AI** – content safety filtering on both the query (pre) and the generated answer (post).
- **Multi-channel delivery** – one RAG core serves API, web, Teams, BI dashboards, and file exports.

---

## 5. Technology Stack

| Category | Technology |
|---|---|
| Ingestion | SharePoint, Blob Storage, Email, Web, FTP/SFTP |
| Orchestration | Azure Data Factory, Azure Functions, Logic Apps |
| OCR / Layout | Azure AI Document Intelligence |
| LLM / Embeddings | Azure OpenAI (GPT-4o, text-embedding-3-small) |
| Search | Azure AI Search (hybrid vector + BM25) |
| Metadata | Cosmos DB |
| Files | Azure Blob Storage |
| Audit | SQL Database |
| Cache | Redis |
| Serving | FastAPI/Flask, React/Angular, Power BI, Microsoft Teams |
```mermaid
graph TB
    subgraph "📥 Ingestion Layer"
        A1[SharePoint]
        A2[Azure Blob Storage]
        A3[Email Attachments]
        A4[Web Upload]
        A5[FTP/SFTP]
    end
    
    subgraph "🔄 Orchestration Layer"
        B1[Azure Data Factory<br/>Pipeline Orchestration]
        B2[Azure Functions<br/>Event-Driven Triggers]
        B3[Logic Apps<br/>Workflow Automation]
    end
    
    subgraph "📄 PDF Pre-Processing"
        C1[PDF Validation<br/>Format Check]
        C2[Image Enhancement<br/>Deskew/Denoise]
        C3[Page Segmentation<br/>Multi-page Split]
        C4[Password Removal<br/>Decryption]
    end
    
    subgraph "🔍 OCR & Document Intelligence"
        D1[Azure AI Document Intelligence<br/>Layout Analysis]
        D2[OCR Engine<br/>Text Recognition]
        D3[Table Extraction<br/>Structure Detection]
        D4[Figure/Chart Detection<br/>Image Analysis]
        D5[Handwriting Recognition<br/>ICR]
    end
    
    subgraph "🧹 Post-Processing & Validation"
        E1[Text Normalization<br/>Unicode Cleanup]
        E2[Language Detection<br/>Multi-language Support]
        E3[Confidence Scoring<br/>Quality Metrics]
        E4[Human-in-the-Loop<br/>Validation Queue]
        E5[Metadata Extraction<br/>Author/Date/Tags]
    end
    
    subgraph "🧠 Gen AI Processing"
        F1[Semantic Chunking<br/>500-1000 tokens]
        F2[Embedding Generation<br/>Azure OpenAI]
        F3[Summarization<br/>GPT-4o]
        F4[Entity Extraction<br/>NER]
        F5[Classification<br/>Document Type]
    end
    
    subgraph "💾 Storage Layer"
        G1[Azure AI Search<br/>Vector + Keyword Index]
        G2[Cosmos DB<br/>Document Metadata]
        G3[Blob Storage<br/>Original PDFs]
        G4[SQL Database<br/>Audit Logs]
        G5[Redis Cache<br/>Frequent Queries]
    end
    
    subgraph "🔎 Query & Retrieval"
        H1[Hybrid Search<br/>Vector + BM25]
        H2[RAG Pipeline<br/>Context Assembly]
        H3[Content Safety<br/>Pre/Post Filtering]
        H4[Response Generation<br/>GPT-4o]
    end
    
    subgraph "📤 Output & Integration"
        I1[REST API<br/>FastAPI/Flask]
        I2[Web UI<br/>React/Angular]
        I3[Power BI<br/>Analytics Dashboard]
        I4[Microsoft Teams<br/>Bot Integration]
        I5[Export Formats<br/>JSON/CSV/Markdown]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B2
    A5 --> B1
    
    B1 --> C1
    B2 --> C1
    B3 --> C1
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D1
    D1 --> D2
    D1 --> D3
    D1 --> D4
    D1 --> D5
    
    D2 --> E1
    D3 --> E1
    D4 --> E1
    D5 --> E1
    
    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> E5
    
    E5 --> F1
    F1 --> F2
    F1 --> F3
    F1 --> F4
    F1 --> F5
    
    F2 --> G1
    F3 --> G2
    F4 --> G2
    F5 --> G2
    C1 --> G3
    E3 --> G4
    
    G1 --> H1
    H1 --> H2
    H2 --> H3
    H3 --> H4
    
    H4 --> I1
    H4 --> I2
    G2 --> I3
    H4 --> I4
    H4 --> I5
```mermaid
