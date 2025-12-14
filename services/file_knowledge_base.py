"""
File Knowledge Base Service

Persistent knowledge base for uploaded Excel files.
Tracks file metadata, column schemas, and data summaries.
Adapted from excelaiagent's knowledge_base.py
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import hashlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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
        
        # Initialize OpenAI client for summary generation (optional)
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client for summaries: {e}")
    
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
        file_hash: Optional[str] = None,
        generate_summary: bool = True
    ) -> Dict:
        """
        Index an Excel file and store metadata
        
        Args:
            file_path: Path to the file
            df: DataFrame with the file data
            file_hash: Optional file hash (will be calculated if not provided)
            generate_summary: Whether to generate LLM summary (default: True)
            
        Returns:
            File metadata dictionary
        """
        file_name = Path(file_path).name
        
        # Check if metadata already exists
        existing_metadata = self.metadata.get(file_name)
        
        # Calculate file hash if not provided
        if not file_hash:
            file_hash = self._calculate_file_hash(file_path)
        
        # Use sample for large files to reduce memory usage (max 1000 rows for metadata extraction)
        MAX_ROWS_FOR_METADATA = 1000
        metadata_df = df.head(MAX_ROWS_FOR_METADATA) if len(df) > MAX_ROWS_FOR_METADATA else df
        
        # Analyze columns (using sample for large files)
        column_info = []
        for col in metadata_df.columns:
            col_data = metadata_df[col]
            column_info.append({
                "name": str(col),
                "dtype": str(col_data.dtype),
                "null_count": int(col_data.isnull().sum()),
                "unique_count": int(col_data.nunique()),
                "sample_values": self._get_sample_values(col_data, max_samples=5)
            })
        
        # Generate LLM summary if requested and not already cached
        summary = None
        if generate_summary:
            if existing_metadata and existing_metadata.get("summary"):
                # Use cached summary
                summary = existing_metadata.get("summary")
                logger.debug(f"Using cached summary for {file_name}")
            else:
                # Generate new summary
                summary = self.generate_summary(file_path, df)
                if summary:
                    logger.info(f"Generated new summary for {file_name}")
        
        file_metadata = {
            "file_name": file_name,
            "file_path": file_path,
            "file_hash": file_hash,
            "row_count": len(df),  # Store actual row count, not sample
            "column_count": len(df.columns),
            "columns": column_info,
            "indexed_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        # Add summary if available
        if summary:
            file_metadata["summary"] = summary
        
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
    
    def delete_file_metadata(self, file_name: str) -> bool:
        """
        Delete metadata for a specific file
        
        Args:
            file_name: Name of the file to delete metadata for
            
        Returns:
            True if deleted, False if not found
        """
        if file_name in self.metadata:
            del self.metadata[file_name]
            self._save_metadata()
            logger.info(f"Deleted metadata for: {file_name}")
            return True
        return False
    
    def cleanup_expired_metadata(self, days: int = 1) -> int:
        """
        Delete metadata for files not accessed in specified days
        
        Args:
            days: Number of days of inactivity before deletion (default: 1 for daily cleanup)
            
        Returns:
            Number of metadata entries deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        files_to_delete = []
        
        for file_name, metadata in self.metadata.items():
            last_accessed_str = metadata.get("last_accessed")
            if last_accessed_str:
                try:
                    last_accessed = datetime.fromisoformat(last_accessed_str)
                    if last_accessed < cutoff_date:
                        files_to_delete.append(file_name)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid last_accessed date for {file_name}: {e}")
                    # If date is invalid, consider it old and delete
                    files_to_delete.append(file_name)
            else:
                # No last_accessed date, check indexed_at
                indexed_at_str = metadata.get("indexed_at")
                if indexed_at_str:
                    try:
                        indexed_at = datetime.fromisoformat(indexed_at_str)
                        if indexed_at < cutoff_date:
                            files_to_delete.append(file_name)
                    except (ValueError, TypeError):
                        # If both dates are invalid, delete
                        files_to_delete.append(file_name)
                else:
                    # No dates at all, delete
                    files_to_delete.append(file_name)
        
        # Delete expired entries
        for file_name in files_to_delete:
            if file_name in self.metadata:
                del self.metadata[file_name]
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_metadata()
            logger.info(f"Cleaned up {deleted_count} expired metadata entries (older than {days} days)")
        
        return deleted_count
    
    def cleanup_missing_files(self, base_path: Optional[str] = None) -> int:
        """
        Delete metadata for files that no longer exist on disk
        
        Args:
            base_path: Base path to check for files (if None, uses file_path from metadata)
            
        Returns:
            Number of metadata entries deleted
        """
        deleted_count = 0
        files_to_delete = []
        
        for file_name, metadata in self.metadata.items():
            file_path = metadata.get("file_path")
            
            # If no file_path in metadata, try to construct from base_path
            if not file_path and base_path:
                file_path = os.path.join(base_path, file_name)
            elif not file_path:
                # No way to check, skip
                continue
            
            # Check if file exists
            if not os.path.exists(file_path):
                files_to_delete.append(file_name)
                logger.debug(f"File not found, marking for deletion: {file_path}")
        
        # Delete metadata for missing files
        for file_name in files_to_delete:
            if file_name in self.metadata:
                del self.metadata[file_name]
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_metadata()
            logger.info(f"Cleaned up {deleted_count} metadata entries for missing files")
        
        return deleted_count
    
    def cleanup_all(self, days: int = 1, check_missing_files: bool = True, base_path: Optional[str] = None) -> Dict[str, int]:
        """
        Comprehensive cleanup: removes expired and missing file metadata
        
        Args:
            days: Days of inactivity before deletion (default: 1 for daily cleanup)
            check_missing_files: Whether to check for missing files (default: True)
            base_path: Base path for file existence check (optional)
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "expired_deleted": 0,
            "missing_deleted": 0,
            "total_deleted": 0
        }
        
        # Cleanup expired metadata
        stats["expired_deleted"] = self.cleanup_expired_metadata(days=days)
        
        # Cleanup missing files
        if check_missing_files:
            stats["missing_deleted"] = self.cleanup_missing_files(base_path=base_path)
        
        stats["total_deleted"] = stats["expired_deleted"] + stats["missing_deleted"]
        
        if stats["total_deleted"] > 0:
            logger.info(
                f"Cleanup complete: {stats['expired_deleted']} expired, "
                f"{stats['missing_deleted']} missing, {stats['total_deleted']} total deleted"
            )
        
        return stats
    
    def get_metadata_stats(self) -> Dict[str, any]:
        """
        Get statistics about stored metadata
        
        Returns:
            Dictionary with metadata statistics
        """
        total_files = len(self.metadata)
        
        # Count by age
        now = datetime.now()
        files_by_age = {
            "last_7_days": 0,
            "last_30_days": 0,
            "last_90_days": 0,
            "older_than_90_days": 0,
            "no_date": 0
        }
        
        total_size = 0
        files_with_summaries = 0
        
        for file_name, metadata in self.metadata.items():
            # Check file size if available
            file_path = metadata.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass
            
            # Count summaries
            if metadata.get("summary"):
                files_with_summaries += 1
            
            # Count by age
            last_accessed_str = metadata.get("last_accessed")
            if last_accessed_str:
                try:
                    last_accessed = datetime.fromisoformat(last_accessed_str)
                    age_days = (now - last_accessed).days
                    
                    if age_days <= 7:
                        files_by_age["last_7_days"] += 1
                    elif age_days <= 30:
                        files_by_age["last_30_days"] += 1
                    elif age_days <= 90:
                        files_by_age["last_90_days"] += 1
                    else:
                        files_by_age["older_than_90_days"] += 1
                except (ValueError, TypeError):
                    files_by_age["no_date"] += 1
            else:
                files_by_age["no_date"] += 1
        
        return {
            "total_files": total_files,
            "files_with_summaries": files_with_summaries,
            "files_by_age": files_by_age,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size > 0 else 0
        }
    
    def detect_patterns(self, col_data: pd.Series, col_name: str) -> Dict:
        """
        Detect data patterns without domain assumptions (lightweight, sample-based)
        
        Args:
            col_data: Column data series
            col_name: Column name
            
        Returns:
            Dictionary with pattern information
        """
        patterns = {}
        
        # Temporal patterns
        if col_data.dtype == 'datetime64[ns]' or 'date' in str(col_name).lower() or 'time' in str(col_name).lower():
            patterns["type"] = "temporal"
            if len(col_data) > 0:
                try:
                    patterns["range"] = {
                        "earliest": str(col_data.min()),
                        "latest": str(col_data.max())
                    }
                except Exception:
                    pass
        
        # Numeric patterns
        elif col_data.dtype in ['int64', 'float64']:
            patterns["type"] = "numeric"
            try:
                patterns["range"] = {
                    "min": float(col_data.min()),
                    "max": float(col_data.max())
                }
                if len(col_data) > 0:
                    patterns["mean"] = float(col_data.mean())
            except Exception:
                pass
            
            # Currency detection (any domain)
            sample_str = str(col_data.head(1).values[0]) if len(col_data) > 0 else ""
            if any(symbol in sample_str for symbol in ['$', '€', '₹', '£', '¥']):
                patterns["format"] = "currency"
            
            # Identifier detection (any domain)
            if col_data.nunique() == len(col_data) and col_data.dtype == 'int64':
                patterns["likely_identifier"] = True
        
        # Categorical vs text
        elif col_data.dtype == 'object':
            unique_ratio = col_data.nunique() / len(col_data) if len(col_data) > 0 else 0
            if unique_ratio < 0.2:  # Less than 20% unique = categorical
                patterns["type"] = "categorical"
                try:
                    patterns["top_categories"] = col_data.value_counts().head(5).to_dict()
                except Exception:
                    pass
            else:
                patterns["type"] = "text"
        
        return patterns
    
    def generate_summary(self, file_path: str, df: pd.DataFrame) -> Optional[str]:
        """
        Generate domain-agnostic LLM summary for ANY Excel file type
        
        Args:
            file_path: Path to the file
            df: DataFrame with file data (may be limited to 1000 rows)
            
        Returns:
            Semantic summary string or None if generation fails
        """
        if not self.openai_client:
            logger.debug("OpenAI client not available, skipping summary generation")
            return None
        
        try:
            # Use sample for large files (max 1000 rows for analysis)
            MAX_ROWS_FOR_ANALYSIS = 1000
            analysis_df = df.head(MAX_ROWS_FOR_ANALYSIS) if len(df) > MAX_ROWS_FOR_ANALYSIS else df
            
            # Build column analysis with pattern detection
            column_analysis = []
            for col in analysis_df.columns:
                col_data = analysis_df[col]
                patterns = self.detect_patterns(col_data, str(col))
                
                col_info = {
                    "name": str(col),
                    "data_type": str(col_data.dtype),
                    "unique_count": int(col_data.nunique()),
                    "null_count": int(col_data.isnull().sum()),
                    "sample_values": self._get_sample_values(col_data, max_samples=5),
                    "patterns": patterns
                }
                
                # Add numeric range if available
                if col_data.dtype in ['int64', 'float64'] and len(col_data) > 0:
                    try:
                        col_info["numeric_range"] = {
                            "min": float(col_data.min()),
                            "max": float(col_data.max())
                        }
                    except Exception:
                        pass
                
                column_analysis.append(col_info)
            
            # Get diverse sample rows (first, middle, last if available)
            sample_rows = []
            if len(analysis_df) > 0:
                indices = [0]
                if len(analysis_df) > 1:
                    indices.append(len(analysis_df) // 2)
                if len(analysis_df) > 2:
                    indices.append(len(analysis_df) - 1)
                
                for idx in indices[:5]:  # Max 5 samples
                    row_dict = {}
                    for col in analysis_df.columns:
                        val = analysis_df.iloc[idx][col]
                        if pd.isna(val):
                            row_dict[str(col)] = None
                        elif isinstance(val, (pd.Timestamp, pd.DatetimeTZDtype)):
                            row_dict[str(col)] = str(val)
                        elif hasattr(val, 'item'):
                            row_dict[str(col)] = val.item()
                        else:
                            row_dict[str(col)] = str(val)[:200]  # Limit length
                    sample_rows.append(row_dict)
            
            # Build domain-agnostic prompt
            prompt = f"""Analyze this Excel file and generate a semantic summary that helps an AI assistant understand the file's structure and data patterns. DO NOT assume any specific business domain - analyze based purely on column names, data types, and sample values.

FILE INFORMATION:
- File name: {Path(file_path).name}
- Total rows: {len(df):,}
- Total columns: {len(df.columns)}

COLUMN ANALYSIS:
{json.dumps(column_analysis, indent=2, default=str)}

SAMPLE DATA (representative rows):
{json.dumps(sample_rows, indent=2, default=str)}

YOUR TASK:
Generate a concise, domain-agnostic summary (60-80 words) that describes:

1. **Data Structure**: What types of data are present? (temporal, numeric, categorical, text, identifiers)
2. **Column Roles**: What role does each column likely play? (identifiers, measurements, categories, descriptions, dates, etc.)
3. **Data Patterns**: What patterns are visible? (ranges, formats, relationships between columns)
4. **File Purpose**: What kind of dataset is this? (infer from structure, not assume domain)

IMPORTANT GUIDELINES:
- DO NOT assume it's financial/sales data unless column names explicitly indicate it
- DO NOT use domain-specific terms unless clearly evident from column names
- Focus on DATA STRUCTURE and PATTERNS, not business context
- Use generic terms: "dataset", "records", "measurements", "categories", "identifiers"
- If column names suggest a domain (e.g., "Patient ID", "Temperature", "Product Code"), mention it, but don't assume
- Describe what the data CONTAINS, not what it's USED FOR

OUTPUT FORMAT:
Write only the summary text (60-80 words), no explanations. Be specific about data types and patterns, but generic about domain.

Generate the summary now:"""
            
            # Call LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert data structure analyst. You analyze Excel files across ALL domains (scientific, business, medical, educational, etc.) without assuming any specific domain. Focus on data types, patterns, and structure, not business context."
                    },
                    {"role": "user", "content": prompt}
                ],
                # Note: GPT-5 models only support default parameters
                max_completion_tokens=250
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary for {Path(file_path).name}: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return None

