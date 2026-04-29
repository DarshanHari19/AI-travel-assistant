#!/usr/bin/env python3
"""
RAG Retriever for Strategic Travel Intelligence
Loads city travel guides AND airport intelligence for comprehensive travel planning
Uses LangChain and FAISS to retrieve logistics, patterns, and insider knowledge
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document

# Configure logging
logger = logging.getLogger(__name__)

# Global vector store instance
_vector_store: Optional[FAISS] = None


def initialize_vector_store(data_path: str = None, api_key: str = None) -> FAISS:
    """
    Initialize FAISS vector store with travel intelligence documents.
    Loads from both city_guides AND airport_guides for comprehensive knowledge.
    
    Args:
        data_path: Path to data directory (defaults to ./data)
        api_key: OpenAI API key for embeddings
        
    Returns:
        FAISS vector store instance with combined city + airport intelligence
    """
    global _vector_store
    
    if _vector_store is not None:
        logger.info("Vector store already initialized, returning cached instance")
        return _vector_store
    
    # Default data path - now points to parent data/ directory
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), "data")
    
    logger.info(f"Initializing vector store from: {data_path}")
    
    # Define subdirectories to load
    subdirs = ["city_guides", "airport_guides"]
    all_documents = []
    
    for subdir in subdirs:
        subdir_path = os.path.join(data_path, subdir)
        
        # Check if directory exists
        if not os.path.exists(subdir_path):
            logger.warning(f"Directory not found (skipping): {subdir_path}")
            continue
        
        # Load markdown files from this subdirectory
        loader = DirectoryLoader(
            subdir_path,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        
        docs = loader.load()
        logger.info(f"✓ Loaded {len(docs)} documents from {subdir}/")
        
        # Tag documents with category metadata
        for doc in docs:
            doc.metadata["category"] = subdir.replace("_", " ").title()
        
        all_documents.extend(docs)
    
    if len(all_documents) == 0:
        raise ValueError(f"No travel intelligence documents found in {data_path}")
    
    logger.info(f"Total documents loaded: {len(all_documents)}")
    
    # Split documents by markdown headers for better semantic chunking
    headers_to_split_on = [
        ("#", "Title"),
        ("##", "Section"),
        ("###", "Subsection"),
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    # Split all documents
    split_docs = []
    for doc in all_documents:
        # Extract location name from filename (city or airport code)
        filename = Path(doc.metadata.get("source", "")).stem
        location_name = filename.replace("_", " ").upper()
        
        # Detect if this is an airport code (3 letters, all caps)
        if len(filename) == 3 and filename.isalpha():
            doc.metadata["type"] = "airport"
            doc.metadata["location"] = location_name  # e.g., "JFK"
        else:
            doc.metadata["type"] = "city"
            doc.metadata["location"] = location_name.title()  # e.g., "New York"
        
        # Split the document
        splits = markdown_splitter.split_text(doc.page_content)
        
        # Transfer metadata to all splits
        for split in splits:
            split.metadata.update({
                "type": doc.metadata["type"],
                "location": doc.metadata["location"],
                "category": doc.metadata["category"],
                "source": doc.metadata.get("source", "")
            })
        
        split_docs.extend(splits)
    
    logger.info(f"✓ Created {len(split_docs)} document chunks after semantic splitting")
    
    # Create embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    
    # Create FAISS vector store
    _vector_store = FAISS.from_documents(split_docs, embeddings)
    logger.info("✓ FAISS vector store initialized with city + airport intelligence")
    
    return _vector_store


def search_travel_knowledge(query: str, k: int = 4) -> List[Document]:
    """
    Search travel intelligence (cities + airports) using semantic similarity.
    
    Args:
        query: Search query (e.g., "JFK terminal 4 transfer times", "Tokyo weather patterns")
        k: Number of results to return (default: 4 for city + airport coverage)
        
    Returns:
        List of relevant document chunks with metadata
    """
    if _vector_store is None:
        raise RuntimeError("Vector store not initialized. Call initialize_vector_store() first.")
    
    logger.info(f"Searching travel knowledge for: {query}")
    results = _vector_store.similarity_search(query, k=k)
    logger.info(f"Found {len(results)} relevant chunks")
    
    return results


def format_search_results(results: List[Document]) -> str:
    """
    Format search results into a readable string with metadata.
    
    Args:
        results: List of document chunks
        
    Returns:
        Formatted string with search results and source attribution
    """
    if not results:
        return "No relevant travel intelligence found."
    
    formatted = []
    for i, doc in enumerate(results, 1):
        location = doc.metadata.get("location", "Unknown")
        doc_type = doc.metadata.get("type", "guide")
        category = doc.metadata.get("category", "Travel Guides")
        content = doc.page_content.strip()
        
        # Add source header with metadata
        source_header = f"**Source {i}: {location}** ({category} - {doc_type.title()})"
        formatted.append(f"{source_header}\n{content}")
    
    return "\n\n---\n\n".join(formatted)


# Convenience function for direct querying
def query_travel_knowledge(query: str, k: int = 4) -> str:
    """
    Query travel intelligence and return formatted results.
    Searches across city guides AND airport intelligence.
    
    Args:
        query: Search query
        k: Number of results to return (default: 4)
        
    Returns:
        Formatted search results as string
        
    Raises:
        RuntimeError: If vector store is not initialized
        
    Examples:
        >>> query_travel_knowledge("JFK terminal transfer times")
        >>> query_travel_knowledge("London transportation in rain")
        >>> query_travel_knowledge("Tokyo typhoon season")
    """
    try:
        results = search_travel_knowledge(query, k=k)
        return format_search_results(results)
    except RuntimeError as e:
        # Re-raise initialization errors
        logger.error(f"Vector store error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error querying travel knowledge: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to query travel intelligence: {str(e)}") from e


if __name__ == "__main__":
    # Test the retriever
    logging.basicConfig(level=logging.INFO)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize vector store with combined data
    initialize_vector_store(api_key=api_key)
    
    # Test queries - both city and airport intelligence
    test_queries = [
        "JFK terminal 4 transfer times to terminal 5",
        "JFK security wait times in the morning", 
        "Best transportation from JFK to Manhattan",
        "What should I know about typhoons in Tokyo?",
        "London fog and flight delays",
        "New York winter storms",
        "Best transport in heavy rain London"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        result = query_travel_knowledge(query, k=2)
        print(result)
        result = query_city_guides(query, k=2)
        print(result)
