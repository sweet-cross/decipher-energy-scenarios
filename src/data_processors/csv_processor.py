import pandas as pd
import os
from typing import Dict, List, Optional, Tuple
import glob
from pathlib import Path

class CSVProcessor:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.synthesis_path = os.path.join(data_path, "extracted", "synthesis")
        self.transformation_path = os.path.join(data_path, "extracted", "transformation")
        self._cache = {}
        
    def get_available_files(self) -> Dict[str, List[str]]:
        """Get list of available CSV files organized by category."""
        files = {
            "synthesis": [],
            "transformation": []
        }
        
        if os.path.exists(self.synthesis_path):
            files["synthesis"] = [f for f in os.listdir(self.synthesis_path) if f.endswith('.csv')]
            
        if os.path.exists(self.transformation_path):
            files["transformation"] = [f for f in os.listdir(self.transformation_path) if f.endswith('.csv')]
            
        return files
    
    def load_csv(self, filename: str, category: str = "synthesis") -> pd.DataFrame:
        """Load a specific CSV file."""
        cache_key = f"{category}_{filename}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        if category == "synthesis":
            file_path = os.path.join(self.synthesis_path, filename)
        elif category == "transformation":
            file_path = os.path.join(self.transformation_path, filename)
        else:
            raise ValueError("Category must be 'synthesis' or 'transformation'")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not found in {category} category")
            
        df = pd.read_csv(file_path)
        self._cache[cache_key] = df
        return df
    
    def search_data_by_keywords(self, keywords: List[str], category: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """Search for data files containing specific keywords."""
        results = {}
        files = self.get_available_files()
        
        categories_to_search = [category] if category else ["synthesis", "transformation"]
        
        for cat in categories_to_search:
            for filename in files.get(cat, []):
                # Check if any keyword is in filename
                if any(keyword.lower() in filename.lower() for keyword in keywords):
                    try:
                        df = self.load_csv(filename, cat)
                        results[f"{cat}/{filename}"] = df
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
                        
        return results
    
    def get_scenarios_and_variants(self, filename: str, category: str = "synthesis") -> Tuple[List[str], List[str]]:
        """Extract unique scenarios and variants from a CSV file."""
        df = self.load_csv(filename, category)
        scenarios = df['scenario'].unique().tolist() if 'scenario' in df.columns else []
        variants = df['variant'].unique().tolist() if 'variant' in df.columns else []
        return scenarios, variants
    
    def filter_data(self, filename: str, category: str = "synthesis", 
                   scenario: Optional[str] = None, variant: Optional[str] = None,
                   year_range: Optional[Tuple[int, int]] = None) -> pd.DataFrame:
        """Filter data by scenario, variant, and year range."""
        df = self.load_csv(filename, category)
        
        if scenario and 'scenario' in df.columns:
            df = df[df['scenario'] == scenario]
            
        if variant and 'variant' in df.columns:
            df = df[df['variant'] == variant]
            
        if year_range and 'year' in df.columns:
            start_year, end_year = year_range
            df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
            
        return df
    
    def get_data_summary(self, filename: str, category: str = "synthesis") -> Dict[str, any]:
        """Get summary statistics for a data file."""
        df = self.load_csv(filename, category)
        
        summary = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "scenarios": df['scenario'].unique().tolist() if 'scenario' in df.columns else [],
            "variants": df['variant'].unique().tolist() if 'variant' in df.columns else [],
            "year_range": [int(df['year'].min()), int(df['year'].max())] if 'year' in df.columns else None,
            "variables": df['variable'].unique().tolist() if 'variable' in df.columns else [],
            "units": df['unit'].unique().tolist() if 'unit' in df.columns else []
        }
        
        return summary
    
    def compare_scenarios(self, filename: str, variable: str, 
                         scenarios: List[str], category: str = "synthesis") -> pd.DataFrame:
        """Compare specific variable across multiple scenarios."""
        df = self.load_csv(filename, category)
        
        if 'variable' in df.columns:
            df = df[df['variable'] == variable]
        
        if scenarios and 'scenario' in df.columns:
            df = df[df['scenario'].isin(scenarios)]
            
        return df