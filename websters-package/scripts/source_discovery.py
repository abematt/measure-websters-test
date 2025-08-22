"""
Convention-based source discovery system for auto-discovering data sources.
Walks the data/sources directory tree and builds source metadata.
"""
import os
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DataSource:
    """Represents a discovered data source with its metadata and file paths"""
    datatype: str  # e.g., "appusage.android.usage"
    category: str  # e.g., "appusage"
    platform: str  # e.g., "android"
    subtype: Optional[str] = None  # e.g., "usage"
    manifest_path: Optional[str] = None
    schema_path: Optional[str] = None
    samples_path: Optional[str] = None
    events_path: Optional[str] = None
    description: str = ""
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    sample_limit: int = 50
    metadata: Dict[str, Any] = field(default_factory=dict)


class SourceDiscovery:
    """Auto-discovers data sources using directory conventions"""
    
    def __init__(self, sources_root: str):
        self.sources_root = Path(sources_root)
        self.discovered_sources: List[DataSource] = []
    
    def discover_sources(self) -> List[DataSource]:
        """Walk the sources directory and discover all data sources"""
        self.discovered_sources = []
        
        if not self.sources_root.exists():
            raise FileNotFoundError(f"Sources root not found: {self.sources_root}")
        
        # Walk through category directories
        for category_path in self.sources_root.iterdir():
            if not category_path.is_dir():
                continue
                
            category = category_path.name
            
            # Walk through platform directories
            for platform_path in category_path.iterdir():
                if not platform_path.is_dir():
                    continue
                    
                platform = platform_path.name
                
                # Check if this platform has direct source files or subtypes
                if self._has_source_files(platform_path):
                    # Direct source (e.g., social/tiktok/)
                    source = self._create_source(
                        path=platform_path,
                        category=category,
                        platform=platform
                    )
                    if source:
                        self.discovered_sources.append(source)
                else:
                    # Has subtypes (e.g., appusage/ios/usage/)
                    for subtype_path in platform_path.iterdir():
                        if not subtype_path.is_dir():
                            continue
                            
                        subtype = subtype_path.name
                        source = self._create_source(
                            path=subtype_path,
                            category=category,
                            platform=platform,
                            subtype=subtype
                        )
                        if source:
                            self.discovered_sources.append(source)
        
        return self.discovered_sources
    
    def _has_source_files(self, path: Path) -> bool:
        """Check if directory contains source files (schema.csv, samples.csv)"""
        return (path / "schema.csv").exists() or (path / "samples.csv").exists()
    
    def _create_source(self, path: Path, category: str, platform: str, 
                      subtype: Optional[str] = None) -> Optional[DataSource]:
        """Create a DataSource object from a directory"""
        # Build datatype identifier
        parts = [category, platform]
        if subtype:
            parts.append(subtype)
        datatype = ".".join(parts)
        
        # Create source object
        source = DataSource(
            datatype=datatype,
            category=category,
            platform=platform,
            subtype=subtype
        )
        
        # Load manifest if exists
        manifest_path = path / "manifest.yaml"
        if manifest_path.exists():
            source.manifest_path = str(manifest_path)
            self._load_manifest(source, manifest_path)
        
        # Find source files
        schema_path = path / "schema.csv"
        if schema_path.exists():
            source.schema_path = str(schema_path)
            
        samples_path = path / "samples.csv"
        if samples_path.exists():
            source.samples_path = str(samples_path)
            
        events_path = path / "events.csv"
        if events_path.exists():
            source.events_path = str(events_path)
        
        # Only return source if it has at least one data file
        if source.schema_path or source.samples_path or source.events_path:
            return source
        
        return None
    
    def _load_manifest(self, source: DataSource, manifest_path: Path):
        """Load metadata from manifest.yaml file"""
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f) or {}
                
            source.description = manifest.get('description', '')
            source.version = manifest.get('version', '1.0')
            source.tags = manifest.get('tags', [])
            source.sample_limit = manifest.get('sample_limit', 50)
            source.metadata = manifest.get('metadata', {})
            
        except Exception as e:
            print(f"Warning: Failed to load manifest {manifest_path}: {e}")
    
    def get_sources_by_category(self, category: str) -> List[DataSource]:
        """Get all sources for a specific category"""
        return [s for s in self.discovered_sources if s.category == category]
    
    def get_sources_by_platform(self, platform: str) -> List[DataSource]:
        """Get all sources for a specific platform"""
        return [s for s in self.discovered_sources if s.platform == platform]
    
    def get_sources_by_tag(self, tag: str) -> List[DataSource]:
        """Get all sources with a specific tag"""
        return [s for s in self.discovered_sources if tag in s.tags]
    
    def to_config_dict(self) -> Dict[str, Any]:
        """Convert discovered sources to config dictionary format for compatibility"""
        config = {"data_sources": {}}
        
        for source in self.discovered_sources:
            # Build nested structure
            category_dict = config["data_sources"].setdefault(source.category, {})
            
            source_config = {
                "schema_file": source.schema_path,
                "samples_file": source.samples_path,
                "sample_limit": source.sample_limit,
                "description": source.description
            }
            
            if source.events_path:
                source_config["events_file"] = source.events_path
            
            if source.subtype:
                platform_dict = category_dict.setdefault(source.platform, {})
                platform_dict[source.subtype] = source_config
            else:
                category_dict[source.platform] = source_config
        
        return config