"""
Enhanced build_index.py for convention-based system with richer metadata.
Compatible with existing query API but provides enhanced filtering capabilities.
"""
import os
import json
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import Document, VectorStoreIndex, Settings, ServiceContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from source_discovery import SourceDiscovery, DataSource

# Load environment variables
load_dotenv()

class EnhancedIndexBuilder:
    """Builds index with enhanced metadata from convention-based sources"""
    
    def __init__(self, sources_root: str, storage_dir: str):
        self.sources_root = Path(sources_root)
        self.storage_dir = Path(storage_dir)
        self.discovery = SourceDiscovery(sources_root)
        
        # Configure LlamaIndex settings - try different initialization methods
        try:
            # Try with model parameter
            Settings.llm = OpenAI(model="gpt-3.5-turbo")
            Settings.embed_model = OpenAIEmbedding()
        except TypeError:
            # Fallback to no parameters
            Settings.llm = OpenAI()
            Settings.embed_model = OpenAIEmbedding()
    
    def build_index(self):
        """Main build process"""
        print("🔍 Discovering data sources...")
        sources = self.discovery.discover_sources()
        print(f"Found {len(sources)} data sources")
        
        all_docs = []
        
        for source in sources:
            print(f"\n📊 Processing {source.datatype}")
            
            # Process schema files
            if source.schema_path:
                docs = self._process_schema(source)
                all_docs.extend(docs)
                print(f"  ✓ Processed {len(docs)} schema definitions")
            
            # Process event files
            if source.events_path:
                docs = self._process_events(source)
                all_docs.extend(docs)
                print(f"  ✓ Processed {len(docs)} event definitions")
            
            # Process sample files
            if source.samples_path:
                docs = self._process_samples(source)
                all_docs.extend(docs)
                print(f"  ✓ Processed {len(docs)} sample records")
        
        print(f"\n📚 Total documents: {len(all_docs)}")
        
        # Create index
        print("🏗️  Building vector index...")
        node_parser = SimpleNodeParser(
            chunk_size=1024,
            chunk_overlap=50
        )
        nodes = node_parser.get_nodes_from_documents(all_docs)
        
        index = VectorStoreIndex(nodes)
        
        # Persist index
        print(f"💾 Saving index to {self.storage_dir}")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(self.storage_dir))
        
        # Save source metadata for query-time filtering
        self._save_source_metadata(sources)
        
        print("✅ Index build complete!")
    
    def _process_schema(self, source: DataSource) -> List[Document]:
        """Process schema CSV files with enhanced metadata"""
        docs = []
        try:
            df = pd.read_csv(source.schema_path)
            
            for _, row in df.iterrows():
                # Enhanced text with semantic context
                text = f"""Column: {row['Column']}
Type: {row['Type']}
Description: {row['Description']}
Example: {row['Example']}
Data Category: {source.category}
Platform: {source.platform}"""
                
                if source.subtype:
                    text += f"\nSubtype: {source.subtype}"
                
                # Rich metadata for filtering and retrieval
                metadata = {
                    "source": "schema",
                    "source_type": "column_definition",
                    "datatype": source.datatype,
                    "category": source.category,
                    "platform": source.platform,
                    "column_name": row['Column'],
                    "data_type": row['Type'],
                    "version": source.version,
                    "tags": source.tags
                }
                
                if source.subtype:
                    metadata["subtype"] = source.subtype
                
                # Add semantic type hints for better retrieval
                metadata.update(self._infer_semantic_type(row))
                
                docs.append(Document(text=text, metadata=metadata))
                
        except Exception as e:
            print(f"  ⚠️  Error processing schema {source.schema_path}: {e}")
        
        return docs
    
    def _process_events(self, source: DataSource) -> List[Document]:
        """Process event definition files"""
        docs = []
        try:
            df = pd.read_csv(source.events_path)
            
            for _, row in df.iterrows():
                text = f"""Event: {row['Event']}
Description: {row['Description']}
Example: {row.get('Event Data Example', 'N/A')}
Notes: {row.get('Notes', 'N/A')}
Platform: {source.platform}
Category: {source.category}"""
                
                metadata = {
                    "source": "supported_events",
                    "source_type": "event_definition",
                    "datatype": source.datatype,
                    "category": source.category,
                    "platform": source.platform,
                    "event_name": row['Event'],
                    "version": source.version,
                    "tags": source.tags + ["event"]
                }
                
                if source.subtype:
                    metadata["subtype"] = source.subtype
                
                docs.append(Document(text=text, metadata=metadata))
                
        except Exception as e:
            print(f"  ⚠️  Error processing events {source.events_path}: {e}")
        
        return docs
    
    def _process_samples(self, source: DataSource) -> List[Document]:
        """Process sample data files with enhanced context"""
        docs = []
        try:
            df = pd.read_csv(source.samples_path)
            sample_limit = min(source.sample_limit, len(df))
            
            for i, row in df.head(sample_limit).iterrows():
                # Convert row to formatted JSON
                row_dict = row.to_dict()
                text = json.dumps(row_dict, indent=2, default=str)
                
                # Add contextual information
                text = f"""Sample Data - {source.datatype}
Category: {source.category}
Platform: {source.platform}
Record #{i+1}:
{text}"""
                
                metadata = {
                    "source": "raw",
                    "source_type": "sample_data",
                    "datatype": source.datatype,
                    "category": source.category,
                    "platform": source.platform,
                    "record_index": i,
                    "version": source.version,
                    "tags": source.tags + ["sample"]
                }
                
                if source.subtype:
                    metadata["subtype"] = source.subtype
                
                # Add data-specific metadata
                metadata.update(self._extract_sample_metadata(row_dict, source))
                
                docs.append(Document(text=text, metadata=metadata))
                
        except Exception as e:
            print(f"  ⚠️  Error processing samples {source.samples_path}: {e}")
        
        return docs
    
    def _infer_semantic_type(self, schema_row: pd.Series) -> Dict[str, Any]:
        """Infer semantic type from column name and type"""
        semantic_metadata = {}
        
        col_lower = schema_row['Column'].lower()
        type_lower = str(schema_row['Type']).lower()
        
        # Temporal fields
        if any(t in col_lower for t in ['time', 'date', 'timestamp', 'created', 'updated']):
            semantic_metadata['semantic_type'] = 'temporal'
            semantic_metadata['field_category'] = 'time'
        
        # Duration fields
        elif any(t in col_lower for t in ['duration', 'length', 'elapsed']):
            semantic_metadata['semantic_type'] = 'duration'
            semantic_metadata['field_category'] = 'metric'
        
        # Identifier fields
        elif any(t in col_lower for t in ['id', 'uuid', 'key', 'identifier']):
            semantic_metadata['semantic_type'] = 'identifier'
            semantic_metadata['field_category'] = 'key'
        
        # Name/label fields
        elif any(t in col_lower for t in ['name', 'title', 'label']):
            semantic_metadata['semantic_type'] = 'label'
            semantic_metadata['field_category'] = 'text'
        
        # Numeric metrics
        elif 'int' in type_lower or 'float' in type_lower:
            semantic_metadata['semantic_type'] = 'metric'
            semantic_metadata['field_category'] = 'numeric'
        
        return semantic_metadata
    
    def _extract_sample_metadata(self, row_dict: Dict, source: DataSource) -> Dict[str, Any]:
        """Extract metadata from sample data based on source type"""
        metadata = {}
        
        # App usage specific
        if source.category == "appusage":
            if 'app_name' in row_dict:
                metadata['app_name'] = row_dict['app_name']
            if 'duration' in row_dict or 'usage_time' in row_dict:
                metadata['has_duration'] = True
        
        # Social media specific
        elif source.category == "social":
            if 'event' in row_dict:
                metadata['event_type'] = row_dict['event']
        
        # Add timestamp info if present
        for key in ['timestamp', 'created_at', 'date']:
            if key in row_dict:
                metadata['has_timestamp'] = True
                break
        
        return metadata
    
    def _save_source_metadata(self, sources: List[DataSource]):
        """Save source metadata for query-time use"""
        metadata_path = self.storage_dir / "source_metadata.json"
        
        metadata = {
            "sources": [
                {
                    "datatype": s.datatype,
                    "category": s.category,
                    "platform": s.platform,
                    "subtype": s.subtype,
                    "description": s.description,
                    "version": s.version,
                    "tags": s.tags,
                    "has_schema": s.schema_path is not None,
                    "has_samples": s.samples_path is not None,
                    "has_events": s.events_path is not None
                }
                for s in sources
            ],
            "categories": list(set(s.category for s in sources)),
            "platforms": list(set(s.platform for s in sources)),
            "all_tags": list(set(tag for s in sources for tag in s.tags))
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def main():
    """Run the index builder"""
    # Get paths relative to this script
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    sources_root = project_root / "data" / "sources"
    storage_dir = project_root / "index_storage"
    
    builder = EnhancedIndexBuilder(
        sources_root=str(sources_root),
        storage_dir=str(storage_dir)
    )
    
    builder.build_index()


if __name__ == "__main__":
    main()