"""
Training Data Loader

Loads training datasets from Excel files and integrates them into the LLM prompt system.
Supports both keyword and semantic search.
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TrainingDataLoader:
    """Load and manage training datasets for few-shot learning"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize training data loader
        
        Args:
            data_dir: Directory containing training datasets
        """
        self.data_dir = Path(__file__).parent.parent / data_dir
        self.datasets: List[Dict] = []
        self.embedding_service = EmbeddingService()
        self.embeddings_cache: Dict[str, np.ndarray] = {}  # Cache embeddings
        self._load_datasets()
        self._generate_embeddings()
    
    def _load_datasets(self):
        """Load all datasets from the data directory"""
        if not self.data_dir.exists():
            logger.warning(f"Data directory not found: {self.data_dir}")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return
        
        # Look for Excel files
        excel_files = list(self.data_dir.glob("*.xlsx")) + list(self.data_dir.glob("*.xls"))
        
        for file_path in excel_files:
            try:
                examples = self._load_excel_dataset(file_path)
                if examples:
                    self.datasets.extend(examples)
                    logger.info(f"Loaded {len(examples)} examples from {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to load {file_path.name}: {e}")
        
        logger.info(f"Total training examples loaded: {len(self.datasets)}")
    
    def _generate_embeddings(self):
        """Generate embeddings for all training examples"""
        if not self.embedding_service.is_available():
            logger.warning("Embedding service not available. Semantic search will be disabled.")
            return
        
        if not self.datasets:
            return
        
        logger.info("Generating embeddings for training examples...")
        try:
            # Generate embeddings for all prompts
            prompts = [ex["prompt"] for ex in self.datasets]
            embeddings = self.embedding_service.encode_batch(prompts, batch_size=32)
            
            # Store embeddings with examples
            for i, (example, embedding) in enumerate(zip(self.datasets, embeddings)):
                if embedding is not None:
                    example["embedding"] = embedding
                    # Cache by prompt for quick lookup
                    self.embeddings_cache[example["prompt"]] = embedding
            
            logger.info(f"Generated embeddings for {len([e for e in embeddings if e is not None])} examples")
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
    
    def _load_excel_dataset(self, file_path: Path) -> List[Dict]:
        """
        Load examples from an Excel file
        
        Supports multiple formats:
        1. Column A: prompts, Column B: action_plans (JSON strings)
        2. Column A: prompts, Column B: action_plans, Column C: execution_instructions
        3. Multiple sheets with different example types
        """
        examples = []
        
        try:
            # Try reading all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            for sheet_name, df in excel_data.items():
                # Try different column name patterns
                prompt_col = None
                action_plan_col = None
                execution_col = None
                
                # Find prompt column (usually first column or named "prompt", "user_prompt", "input", "user_message")
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower in ["prompt", "user_prompt", "input", "query", "request", "user", "user_message"]:
                        prompt_col = col
                        break
                
                if prompt_col is None and len(df.columns) > 0:
                    prompt_col = df.columns[0]  # Default to first column
                
                # Find action plan column (model_response, action_plan, response, output, json, plan)
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower in ["action_plan", "response", "output", "json", "plan", "model_response"]:
                        action_plan_col = col
                        break
                
                if action_plan_col is None and len(df.columns) > 1:
                    action_plan_col = df.columns[1]  # Default to second column
                
                # Find execution instructions column (optional)
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower in ["execution", "instructions", "execution_instructions", "steps"]:
                        execution_col = col
                        break
                
                # Parse examples
                for idx, row in df.iterrows():
                    try:
                        prompt = str(row[prompt_col]).strip() if prompt_col and pd.notna(row[prompt_col]) else None
                        if not prompt or prompt.lower() in ["nan", "none", ""]:
                            continue
                        
                        # Parse action plan (handles JSON + explanation format)
                        action_plan = None
                        if action_plan_col and pd.notna(row[action_plan_col]):
                            action_plan_str = str(row[action_plan_col]).strip()
                            
                            # Handle format: JSON + explanation (extract JSON part)
                            # Try to find JSON object in the response
                            import re
                            
                            # First, try direct JSON parse
                            try:
                                action_plan = json.loads(action_plan_str)
                            except json.JSONDecodeError:
                                # Try to extract JSON from text (handles "JSON + explanation" format)
                                # Look for JSON object (handles multi-line JSON)
                                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', action_plan_str, re.DOTALL)
                                if json_match:
                                    try:
                                        action_plan = json.loads(json_match.group())
                                    except json.JSONDecodeError:
                                        # Try to find JSON in code blocks
                                        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', action_plan_str, re.DOTALL)
                                        if code_block_match:
                                            try:
                                                action_plan = json.loads(code_block_match.group(1))
                                            except json.JSONDecodeError:
                                                pass
                                
                                if not action_plan:
                                    logger.warning(f"Could not parse action plan for prompt: {prompt[:50]}")
                                    continue
                        
                        if not action_plan:
                            continue
                        
                        # Get execution instructions if available
                        execution_instructions = None
                        if execution_col and pd.notna(row[execution_col]):
                            execution_instructions = str(row[execution_col]).strip()
                        
                        examples.append({
                            "prompt": prompt,
                            "action_plan": action_plan,
                            "execution_instructions": execution_instructions,
                            "source_file": file_path.name,
                            "source_sheet": sheet_name
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing row {idx} in {file_path.name}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
        
        return examples
    
    def get_examples_for_prompt(
        self, 
        user_prompt: str, 
        limit: int = 5,
        categories: Optional[List[str]] = None,
        use_semantic: bool = True
    ) -> List[Dict]:
        """
        Get relevant examples for a user prompt using semantic search
        
        Args:
            user_prompt: User's prompt to find similar examples for
            limit: Maximum number of examples to return
            categories: Optional list of categories to filter by (e.g., ["cleaning", "formulas"])
            use_semantic: Whether to use semantic search (True) or keyword search (False)
            
        Returns:
            List of similar examples
        """
        if not self.datasets:
            return []
        
        # Use semantic search if available, otherwise fall back to keyword
        if use_semantic and self.embedding_service.is_available():
            return self._semantic_search(user_prompt, limit, categories)
        else:
            return self._keyword_search(user_prompt, limit, categories)
    
    def _semantic_search(
        self,
        user_prompt: str,
        limit: int = 5,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """Find examples using semantic similarity"""
        try:
            # Generate embedding for user prompt
            query_embedding = self.embedding_service.encode(user_prompt)
            if query_embedding is None:
                # Fall back to keyword search if embedding fails
                return self._keyword_search(user_prompt, limit, categories)
            
            # Filter by category if specified
            candidates = self.datasets
            if categories:
                candidates = self._filter_by_categories(candidates, categories)
            
            # Prepare candidate embeddings
            candidate_embeddings = []
            for example in candidates:
                # Get embedding from cache or example
                embedding = example.get("embedding")
                if embedding is None:
                    # Generate on-the-fly if not cached
                    embedding = self.embedding_service.encode(example["prompt"])
                    if embedding is not None:
                        example["embedding"] = embedding
                
                if embedding is not None:
                    candidate_embeddings.append((embedding, example))
            
            # Find most similar
            results = self.embedding_service.find_most_similar(
                query_embedding,
                candidate_embeddings,
                top_k=limit * 2  # Get more, then filter
            )
            
            # Extract examples with similarity scores
            scored_examples = []
            for similarity, example in results:
                example_with_score = example.copy()
                example_with_score["similarity_score"] = similarity
                scored_examples.append(example_with_score)
            
            # Filter by minimum similarity threshold (0.3)
            filtered = [ex for ex in scored_examples if ex.get("similarity_score", 0) >= 0.3]
            
            return filtered[:limit]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Fall back to keyword search
            return self._keyword_search(user_prompt, limit, categories)
    
    def _keyword_search(
        self,
        user_prompt: str,
        limit: int = 5,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """Find examples using keyword matching (fallback)"""
        prompt_lower = user_prompt.lower()
        prompt_words = set(prompt_lower.split())
        
        # Filter by category if specified
        filtered_datasets = self._filter_by_categories(self.datasets, categories) if categories else self.datasets
        
        # Score examples by similarity
        scored_examples = []
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        
        for example in filtered_datasets:
            example_prompt = example["prompt"].lower()
            example_words = set(example_prompt.split())
            
            # Count common meaningful words
            common_words = (prompt_words & example_words) - stop_words
            
            if len(common_words) >= 1:  # At least 1 common word
                score = len(common_words)
                scored_examples.append((score, example))
        
        # Sort by score (descending) and return top N
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        
        return [ex[1] for ex in scored_examples[:limit]]
    
    def _filter_by_categories(self, datasets: List[Dict], categories: List[str]) -> List[Dict]:
        """Filter datasets by category keywords"""
        category_keywords = {
            "cleaning": ["clean", "remove", "duplicate", "format"],
            "formulas": ["sum", "average", "count", "formula", "calculate"],
            "sorting": ["sort", "order", "arrange"],
            "filtering": ["filter", "where", "show only"],
            "charts": ["chart", "graph", "visualize", "dashboard"],
            "pivot": ["pivot", "group", "aggregate"]
        }
        
        relevant_keywords = set()
        for cat in categories:
            if cat.lower() in category_keywords:
                relevant_keywords.update(category_keywords[cat.lower()])
        
        if relevant_keywords:
            return [
                ex for ex in datasets
                if any(kw in ex["prompt"].lower() for kw in relevant_keywords)
            ]
        
        return datasets
    
    def get_all_examples(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all training examples
        
        Args:
            limit: Optional limit on number of examples
            
        Returns:
            List of all examples
        """
        if limit:
            return self.datasets[:limit]
        return self.datasets
    
    def reload(self):
        """Reload datasets from disk"""
        self.datasets = []
        self._load_datasets()
    
    def get_statistics(self) -> Dict:
        """Get statistics about loaded datasets"""
        if not self.datasets:
            return {
                "total_examples": 0,
                "sources": {},
                "categories": {}
            }
        
        sources = {}
        for ex in self.datasets:
            source = ex.get("source_file", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_examples": len(self.datasets),
            "sources": sources,
            "sample_prompts": [ex["prompt"][:50] + "..." for ex in self.datasets[:5]]
        }

