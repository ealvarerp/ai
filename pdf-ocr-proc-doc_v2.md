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
