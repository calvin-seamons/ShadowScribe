"""
Vector Store Manager

Handles creation and management of vector stores with embeddings.
"""

import os
import logging
from typing import List, Any
from tqdm import tqdm
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.schema import Document as LangChainDocument
from langchain_community.vectorstores.utils import filter_complex_metadata

from config.settings import Config
from utils.helpers import TokenCounter


class VectorStoreManager:
    """Manages vector store operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.token_counter = TokenCounter()
        
        # Set up OpenAI API key
        api_key = config.openai_api_key
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        elif not os.getenv('OPENAI_API_KEY'):
            self.logger.warning("No OpenAI API key found in environment")
        
        self.embeddings = OpenAIEmbeddings(model=config.embedding_model)
    
    def create_vector_store(self, chunks: List[LangChainDocument]) -> Any:
        """Create and populate vector store with batch processing"""
        self.logger.info(f"🔮 Creating {self.config.vector_store_type} vector store with {len(chunks)} chunks")
        
        # Calculate optimal batch size based on token counts
        total_tokens = sum(chunk.metadata.get('token_count', 0) for chunk in chunks)
        avg_tokens_per_chunk = total_tokens / len(chunks) if chunks else 0
        
        # Aim for ~150k tokens per batch (well under 300k limit)
        batch_size = max(50, min(500, int(150000 / avg_tokens_per_chunk))) if avg_tokens_per_chunk > 0 else 200
        
        self.logger.info(f"📊 Average tokens per chunk: {avg_tokens_per_chunk:.0f}, using batch size: {batch_size}")
        
        # Filter complex metadata from all chunks
        filtered_chunks = []
        for chunk in chunks:
            filtered_metadata = filter_complex_metadata(chunk.metadata)
            filtered_chunk = LangChainDocument(
                page_content=chunk.page_content,
                metadata=filtered_metadata
            )
            filtered_chunks.append(filtered_chunk)
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.vector_store_type.lower() == "chroma":
            return self._create_chroma_store(filtered_chunks, batch_size)
        elif self.config.vector_store_type.lower() == "faiss":
            return self._create_faiss_store(filtered_chunks, batch_size)
        else:
            raise ValueError(f"Unsupported vector store type: {self.config.vector_store_type}")
    
    def _create_chroma_store(self, chunks: List[LangChainDocument], batch_size: int) -> Any:
        """Create ChromaDB vector store with batch processing"""
        self.logger.info(f"📦 Processing in batches of {batch_size} chunks")
        
        vector_store = None
        
        with tqdm(total=len(chunks), desc="Creating embeddings") as pbar:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                try:
                    if vector_store is None:
                        # Create initial store
                        vector_store = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=str(self.config.output_dir),
                            collection_name=self.config.collection_name
                        )
                    else:
                        # Add to existing store
                        vector_store.add_documents(batch)
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    # Continue with next batch
                    pbar.update(len(batch))
        
        if vector_store:
            try:
                vector_store.persist()
            except AttributeError:
                # Newer versions of Chroma auto-persist
                pass
        
        self.logger.info("✅ Vector store created successfully")
        return vector_store
    
    def _create_faiss_store(self, chunks: List[LangChainDocument], batch_size: int) -> Any:
        """Create FAISS vector store with batch processing"""
        self.logger.info(f"📦 Processing in batches of {batch_size} chunks")
        
        # Process first batch to create initial store
        first_batch = chunks[:batch_size]
        vector_store = FAISS.from_documents(
            documents=first_batch,
            embedding=self.embeddings
        )
        
        # Process remaining batches
        with tqdm(total=len(chunks), initial=len(first_batch), desc="Creating embeddings") as pbar:
            pbar.update(len(first_batch))
            
            for i in range(batch_size, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                try:
                    # Create temporary store for batch and merge
                    batch_store = FAISS.from_documents(
                        documents=batch,
                        embedding=self.embeddings
                    )
                    vector_store.merge_from(batch_store)
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    pbar.update(len(batch))
        
        # Save the store
        vector_store.save_local(str(self.config.output_dir))
        
        self.logger.info("✅ Vector store created successfully")
        return vector_store
    
    def load_vector_store(self) -> Any:
        """Load existing vector store"""
        if self.config.vector_store_type.lower() == "chroma":
            return Chroma(
                persist_directory=str(self.config.output_dir),
                embedding_function=self.embeddings,
                collection_name=self.config.collection_name
            )
        elif self.config.vector_store_type.lower() == "faiss":
            return FAISS.load_local(str(self.config.output_dir), self.embeddings)
        else:
            raise ValueError(f"Unsupported vector store type: {self.config.vector_store_type}")


def test_retrieval(vector_store: Any, test_queries: List[str]):
    """Test retrieval with sample queries"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing retrieval system")
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        
        try:
            # Perform similarity search
            results = vector_store.similarity_search(query, k=3)
            
            for i, result in enumerate(results, 1):
                logger.info(f"Result {i}:")
                logger.info(f"  Type: {result.metadata.get('type', 'unknown')}")
                logger.info(f"  Source: {result.metadata.get('source', 'unknown')}")
                logger.info(f"  Name: {result.metadata.get('name', 'unknown')}")
                logger.info(f"  Content preview: {result.page_content[:200]}...")
        except Exception as e:
            logger.error(f"Error testing query '{query}': {e}")
