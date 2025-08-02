"""
File I/O utilities for saving chunks and processing files
"""

import json
import logging
from pathlib import Path
from typing import List
from langchain.schema import Document as LangChainDocument


def save_chunks_to_json(chunks: List[LangChainDocument], output_file: Path, format_type: str = 'json'):
    """Save chunks to JSON or CSV file for inspection"""
    if format_type == 'json':
        chunks_data = []
        for chunk in chunks:
            chunk_data = {
                'content': chunk.page_content[:500] + "..." if len(chunk.page_content) > 500 else chunk.page_content,
                'content_length': len(chunk.page_content),
                'metadata': chunk.metadata
            }
            chunks_data.append(chunk_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    elif format_type == 'csv':
        try:
            import pandas as pd
            
            rows = []
            for chunk in chunks:
                row = {
                    'content_preview': chunk.page_content[:200] + "..." if len(chunk.page_content) > 200 else chunk.page_content,
                    'content_length': len(chunk.page_content),
                    **chunk.metadata
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            csv_file = output_file.with_suffix('.csv')
            df.to_csv(csv_file, index=False)
            
        except ImportError:
            logging.warning("pandas not available, falling back to JSON format")
            save_chunks_to_json(chunks, output_file, 'json')
    
    logging.info(f"💾 Saved {len(chunks)} chunks to {output_file}")
