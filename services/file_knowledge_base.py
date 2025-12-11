"""
File Knowledge Base Service

Persistent knowledge base for uploaded Excel files.
Tracks file metadata, column schemas, and data summaries.
Adapted from excelaiagent's knowledge_base.py
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import hashlib

logger = logging.getLogger(__name__)


class FileKnowledgeBase:
    """Manages persistent file metadata"""
    
    def __init__(self, metadata_file: str = "file_metadata.json"):
        """
        Initialize file knowledge base
        
        Args:
            metadata_file: Path to metadata JSON file
        """
        self.metadata_file = Path(metadata_file)
        self.metadata: Dict = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Metadata file corrupted, will rebuild: {e}")
                # Backup corrupted file
                backup_path = self.metadata_file.with_suffix('.json.bak')
                try:
                    import shutil
                    shutil.copy2(self.metadata_file, backup_path)
                    logger.info(f"Backed up corrupted metadata to: {backup_path}")
                except Exception:
                    pass
                return {}
            except Exception as e:
                logger.error(f"Error loading metadata: {e}", exc_info=True)
                return {}
        return {}
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.debug(f"Metadata saved to: {self.metadata_file}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}", exc_info=True)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for change detection"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate file hash: {e}")
            return ""
    
    def index_file(
        self, 
        file_path: str, 
        df: pd.DataFrame,
        file_hash: Optional[str] = None
    ) -> Dict:
        """
        Index an Excel file and store metadata
        
        Args:
            file_path: Path to the file
            df: DataFrame with the file data
            file_hash: Optional file hash (will be calculated if not provided)
            
        Returns:
            File metadata dictionary
        """
        file_name = Path(file_path).name
        
        # Calculate file hash if not provided
        if not file_hash:
            file_hash = self._calculate_file_hash(file_path)
        
        # Analyze columns
        column_info = []
        for col in df.columns:
            col_data = df[col]
            column_info.append({
                "name": str(col),
                "dtype": str(col_data.dtype),
                "null_count": int(col_data.isnull().sum()),
                "unique_count": int(col_data.nunique()),
                "sample_values": self._get_sample_values(col_data)
            })
        
        file_metadata = {
            "file_name": file_name,
            "file_path": file_path,
            "file_hash": file_hash,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": column_info,
            "indexed_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        # Store by file name (could also use hash as key)
        self.metadata[file_name] = file_metadata
        self._save_metadata()
        
        logger.info(f"Indexed file: {file_name} ({len(df)} rows, {len(df.columns)} columns)")
        return file_metadata
    
    def _get_sample_values(self, col_data: pd.Series, max_samples: int = 3) -> List:
        """Get sample values from a column"""
        try:
            samples = col_data.dropna().head(max_samples).tolist()
            # Convert to serializable format
            serializable = []
            for val in samples:
                if pd.isna(val):
                    continue
                if isinstance(val, (pd.Timestamp, pd.DatetimeTZDtype)):
                    serializable.append(str(val))
                elif hasattr(val, 'item'):  # numpy scalar
                    serializable.append(val.item())
                else:
                    serializable.append(str(val)[:100])  # Limit length
            return serializable
        except Exception:
            return []
    
    def get_file_schema(self, file_name: str) -> Optional[Dict]:
        """
        Get schema for a specific file
        
        Args:
            file_name: Name of the file
            
        Returns:
            File metadata or None if not found
        """
        metadata = self.metadata.get(file_name)
        if metadata:
            # Update last accessed time
            metadata["last_accessed"] = datetime.now().isoformat()
            self._save_metadata()
        return metadata
    
    def search_files(self, query: str) -> List[Dict]:
        """
        Search files by column names or metadata
        
        Args:
            query: Search query (column name or keyword)
            
        Returns:
            List of matching file metadata
        """
        query_lower = query.lower()
        results = []
        
        for file_name, metadata in self.metadata.items():
            # Search in column names
            matching_columns = [
                col for col in metadata.get("columns", [])
                if query_lower in col.get("name", "").lower()
            ]
            
            # Search in file name
            if query_lower in file_name.lower() or matching_columns:
                results.append({
                    "file_name": file_name,
                    "metadata": metadata,
                    "matching_columns": [col["name"] for col in matching_columns]
                })
        
        return results
    
    def get_all_files(self) -> List[Dict]:
        """Get metadata for all indexed files"""
        return [
            {"file_name": name, "metadata": meta}
            for name, meta in self.metadata.items()
        ]
    
    def update_access_time(self, file_name: str):
        """Update last accessed time for a file"""
        if file_name in self.metadata:
            self.metadata[file_name]["last_accessed"] = datetime.now().isoformat()
            self._save_metadata()
    
    def delete_file_metadata(self, file_name: str):
        """Delete metadata for a file"""
        if file_name in self.metadata:
            del self.metadata[file_name]
            self._save_metadata()
            logger.info(f"Deleted metadata for: {file_name}")

