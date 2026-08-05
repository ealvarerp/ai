import os
import io
from typing import List, Dict
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.models import AnalyzeResult, ContentFormat
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

load_dotenv()


class PDFProcessingPipeline:
    """Complete PDF processing pipeline with Azure AI integration."""
    
    def __init__(self):
        # Initialize Azure AI Document Intelligence
        self.doc_intelligence = DocumentIntelligenceClient(
            endpoint=os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_DOC_INTELLIGENCE_KEY"))
        )
        
        # Initialize Azure OpenAI Embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        
        # Initialize Azure AI Search Vector Store
        self.vector_store = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding_function=self.embeddings.embed_query,
        )
        
        # Initialize LLM for RAG
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.2,
        )
    
    # ==========================================
    # STEP 1: PDF EXTRACTION (Azure AI Document Intelligence)
    # ==========================================
    def extract_pdf_content(self, pdf_path: str) -> Dict:
        """
        Extract text, tables, and structure from PDF using Azure AI Document Intelligence.
        Returns structured content with metadata.
        """
        print(f"[1/4] Extracting content from {pdf_path}...")
        
        with open(pdf_path, "rb") as pdf_file:
            poller = self.doc_intelligence.begin_analyze_document(
                "prebuilt-layout",  # Use "prebuilt-read" for text-only
                pdf_file,
                output_content_format=ContentFormat.MARKDOWN  # Get markdown format
            )
            result: AnalyzeResult = poller.result()
        
        # Extract structured content
        extracted_data = {
            "content": result.content,  # Full markdown content
            "tables": [],
            "metadata": {
                "page_count": len(result.pages),
                "language": result.content_locale if hasattr(result, 'content_locale') else "unknown",
            }
        }
        
        # Extract tables if present
        if result.tables:
            for table in result.tables:
                extracted_data["tables"].append({
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": table.cells
                })
        
        print(f"     -> Extracted {extracted_data['metadata']['page_count']} pages")
        return extracted_data
    
    # ==========================================
    # STEP 2: CHUNKING (Semantic/Token-based)
    # ==========================================
    def chunk_content(self, content: str, chunk_size: int = 800, overlap: int = 100) -> List[Document]:
        """
        Split extracted content into semantic chunks using token-based splitting.
        """
        print(f"[2/4] Chunking content (size: {chunk_size} tokens, overlap: {overlap})...")
        
        # Use tiktoken for accurate token counting
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-4o",
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""]  # Prioritize paragraph breaks
        )
        
        chunks = text_splitter.split_text(content)
        
        # Convert to LangChain Documents with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "source": "pdf_document"
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        print(f"     -> Created {len(documents)} chunks")
        return documents
    
    # ==========================================
    # STEP 3: EMBEDDING & INDEXING (Azure OpenAI + AI Search)
    # ==========================================
    def index_documents(self, documents: List[Document]):
        """
        Generate embeddings and store in Azure AI Search with hybrid search capability.
        """
        print(f"[3/4] Generating embeddings and indexing to Azure AI Search...")
        
        # AzureSearch automatically:
        # 1. Calls Azure OpenAI to generate embeddings
        # 2. Creates/updates the search index schema
        # 3. Uploads documents with vectors
        self.vector_store.add_documents(documents=documents)
        
        print(f"     -> Successfully indexed {len(documents)} documents")
    
    # ==========================================
    # STEP 4: RAG QUERY (Hybrid Search + Generation)
    # ==========================================
    def query(self, question: str, top_k: int = 5) -> str:
        """
        Perform hybrid search (vector + keyword) and generate answer with citations.
        """
        print(f"[4/4] Querying: '{question}'")
        
        # Create hybrid retriever (Vector + BM25)
        retriever = self.vector_store.as_retriever(
            search_type="hybrid",
            search_kwargs={"k": top_k}
        )
        
        # Retrieve relevant chunks
        docs = retriever.invoke(question)
        
        # Format context with citations
        context = "\n\n---\n\n".join([
            f"[{i+1}] {doc.page_content}" for i, doc in enumerate(docs)
        ])
        
        # Generate answer using LLM
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Answer the question using ONLY the provided context.
Cite sources using [1], [2], etc.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:""")
        
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})
        
        return answer
    
    # ==========================================
    # FULL PIPELINE EXECUTION
    # ==========================================
    def process_pdf(self, pdf_path: str):
        """Run the complete PDF processing pipeline."""
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path}")
        print(f"{'='*60}\n")
        
        # Step 1: Extract
        extracted = self.extract_pdf_content(pdf_path)
        
        # Step 2: Chunk
        documents = self.chunk_content(extracted["content"])
        
        # Step 3: Index
        self.index_documents(documents)
        
        print(f"\n✅ PDF processing complete! Ready for queries.\n")


# ==========================================
# USAGE EXAMPLE
# ==========================================
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = PDFProcessingPipeline()
    
    # Process a PDF document
    pdf_file = "sample_document.pdf"  # Replace with your PDF path
    pipeline.process_pdf(pdf_file)
    
    # Query the indexed documents
    question = "What is the main topic of this document?"
    answer = pipeline.query(question)
    
    print(f"\n❓ Question: {question}")
    print(f"💡 Answer: {answer}")
