"""
Vector Store Manager

Handles creation and management of vector stores with embeddings.
"""

import os
import logging
import traceback
from typing import List, Any
from tqdm import tqdm
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.schema import Document as LangChainDocument

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
    
    def _filter_metadata_for_vector_store(self, metadata: dict) -> dict:
        """Custom metadata filter that converts lists to strings and handles complex types"""
        filtered = {}
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                filtered[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                filtered[key] = ', '.join(str(item) for item in value)
            elif hasattr(value, '__str__'):
                # Convert other types to strings
                filtered[key] = str(value)
        return filtered
    
    def create_vector_store(self, chunks: List[LangChainDocument], collection_name: str = None) -> Any:
        """Create and populate vector store with batch processing"""
        if collection_name is None:
            collection_name = self.config.collection_name
            
        self.logger.info(f"🔮 Creating {self.config.vector_store_type} vector store '{collection_name}' with {len(chunks)} chunks")
        
        # Debug: Check chunk types at entry
        if chunks:
            self.logger.debug(f"Input chunks - First chunk type: {type(chunks[0])}")
            self.logger.debug(f"Input chunks - First chunk has page_content: {hasattr(chunks[0], 'page_content')}")
            if hasattr(chunks[0], 'page_content'):
                self.logger.debug(f"Input chunks - First chunk page_content length: {len(chunks[0].page_content)}")
        
        # Calculate optimal batch size based on token counts
        total_tokens = sum(chunk.metadata.get('token_count', 0) for chunk in chunks if hasattr(chunk, 'metadata'))
        avg_tokens_per_chunk = total_tokens / len(chunks) if chunks else 0
        
        # Aim for ~150k tokens per batch (well under 300k limit)
        batch_size = max(50, min(500, int(150000 / avg_tokens_per_chunk))) if avg_tokens_per_chunk > 0 else 200
        
        self.logger.info(f"📊 Average tokens per chunk: {avg_tokens_per_chunk:.0f}, using batch size: {batch_size}")
        
        # Filter complex metadata from all chunks
        filtered_chunks = []
        
        # Debug: Log the initial chunk types
        self.logger.info(f"DEBUG: Starting to filter {len(chunks)} chunks")
        if chunks:
            self.logger.info(f"DEBUG: First chunk in list: type={type(chunks[0])}")
            self.logger.info(f"DEBUG: Chunks list type: {type(chunks)}")
        
        for i, chunk in enumerate(chunks):
            try:
                # Debug: Check individual chunk type with detailed logging
                self.logger.debug(f"DEBUG: Processing chunk {i}: type={type(chunk)}")
                
                # Check if chunk is a string (which shouldn't happen)
                if isinstance(chunk, str):
                    self.logger.warning(f"Skipping string chunk at index {i}: {chunk[:100]}...")
                    continue
                
                # Ensure chunk is a Document object
                if not isinstance(chunk, LangChainDocument):
                    self.logger.warning(f"Skipping non-Document chunk at index {i}: {type(chunk)} - {str(chunk)[:100]}")
                    continue
                
                # Debug: Check if chunk has required attributes
                if not hasattr(chunk, 'page_content'):
                    self.logger.warning(f"Chunk {i} missing page_content attribute")
                    continue
                
                # Debug: Test accessing page_content
                try:
                    page_content = chunk.page_content
                    self.logger.debug(f"DEBUG: Chunk {i} page_content length: {len(page_content)}")
                except Exception as e:
                    self.logger.warning(f"Error accessing page_content for chunk {i}: {e}")
                    continue
                    
                # Ensure chunk has metadata
                if not hasattr(chunk, 'metadata') or chunk.metadata is None:
                    chunk.metadata = {}
                
                # Debug: Test accessing metadata
                try:
                    metadata = chunk.metadata
                    self.logger.debug(f"DEBUG: Chunk {i} metadata keys: {list(metadata.keys())}")
                except Exception as e:
                    self.logger.warning(f"Error accessing metadata for chunk {i}: {e}")
                    continue
                
                # Filter complex metadata using our custom filter
                try:
                    filtered_metadata = self._filter_metadata_for_vector_store(metadata)
                    self.logger.debug(f"DEBUG: Chunk {i} filtered metadata keys: {list(filtered_metadata.keys())}")
                except Exception as e:
                    self.logger.warning(f"Error in _filter_metadata_for_vector_store for chunk {i}: {e}")
                    # Fallback to basic filtering
                    filtered_metadata = {k: str(v) for k, v in metadata.items() if v is not None}
                    self.logger.info(f"Using basic filtered metadata for chunk {i}")
                
                # Create filtered chunk
                try:
                    filtered_chunk = LangChainDocument(
                        page_content=page_content,
                        metadata=filtered_metadata
                    )
                    filtered_chunks.append(filtered_chunk)
                    
                    # Debug: Log successful processing
                    if i < 5:  # Only log first 5 for brevity
                        self.logger.info(f"DEBUG: Successfully processed chunk {i}")
                except Exception as e:
                    self.logger.warning(f"Error creating filtered chunk {i}: {e}")
                    continue
                    
            except Exception as e:
                self.logger.warning(f"Skipping chunk due to metadata error: {e}")
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                continue
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.vector_store_type.lower() == "chroma":
            return self._create_chroma_store(filtered_chunks, batch_size, collection_name)
        elif self.config.vector_store_type.lower() == "faiss":
            return self._create_faiss_store(filtered_chunks, batch_size, collection_name)
        else:
            raise ValueError(f"Unsupported vector store type: {self.config.vector_store_type}")
    
    def _create_chroma_store(self, chunks: List[LangChainDocument], batch_size: int, collection_name: str) -> Any:
        """Create ChromaDB vector store with batch processing"""
        self.logger.info(f"📦 Processing in batches of {batch_size} chunks for collection '{collection_name}'")
        
        vector_store = None
        
        with tqdm(total=len(chunks), desc=f"Creating embeddings for {collection_name}") as pbar:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                try:
                    if vector_store is None:
                        # Create initial store
                        vector_store = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=str(self.config.output_dir),
                            collection_name=collection_name
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
    
    def _create_faiss_store(self, chunks: List[LangChainDocument], batch_size: int, collection_name: str) -> Any:
        """Create FAISS vector store with batch processing"""
        self.logger.info(f"📦 Processing in batches of {batch_size} chunks for collection '{collection_name}'")
        
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
        
        # Save the store to a collection-specific directory for FAISS
        faiss_output_dir = self.config.output_dir / collection_name
        faiss_output_dir.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(faiss_output_dir))
        
        self.logger.info("✅ Vector store created successfully")
        return vector_store
    
    def load_vector_store(self, collection_name: str = None) -> Any:
        """Load existing vector store for a specific collection"""
        if collection_name is None:
            collection_name = self.config.collection_name
            
        if self.config.vector_store_type.lower() == "chroma":
            return Chroma(
                persist_directory=str(self.config.output_dir),
                embedding_function=self.embeddings,
                collection_name=collection_name
            )
        elif self.config.vector_store_type.lower() == "faiss":
            # For FAISS, load from collection-specific directory
            faiss_dir = self.config.output_dir / collection_name
            return FAISS.load_local(str(faiss_dir), self.embeddings)
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
