"""
Data Processing & Analysis Tools
Batch semantic compression, lexicon processing, signal aggregation.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
import glob
from typing import Dict, List, Any
from collections import Counter, defaultdict
from datetime import datetime
import re

mcp = FastMCP("DataProcessor")

LEXICON_DIR = os.path.normpath("D:/mcp_servers/lexicons")
STORAGE_DIR = os.path.normpath("D:/mcp_servers/storage")

class LexiconProcessor:
    """Processes and indexes lexicon files."""
    
    def __init__(self, lexicon_dir: str):
        self.lexicon_dir = lexicon_dir
        self.cache = {}
    
    def list_lexicons(self) -> Dict[str, Any]:
        """Lists all available lexicon files."""
        lexicons = {
            'category_files': {},
            'nfo_files': {},
            'readme_files': {},
            'total_files': 0
        }
        
        for file in os.listdir(self.lexicon_dir):
            full_path = os.path.join(self.lexicon_dir, file)
            if os.path.isfile(full_path):
                if file.endswith('.cat'):
                    lexicons['category_files'][file] = os.path.getsize(full_path)
                elif file.endswith('.nfo'):
                    lexicons['nfo_files'][file] = os.path.getsize(full_path)
                elif file.endswith('.txt'):
                    lexicons['readme_files'][file] = os.path.getsize(full_path)
                
                lexicons['total_files'] += 1
        
        return lexicons
    
    def load_lexicon(self, filename: str, limit: int = 1000) -> Dict[str, Any]:
        """Loads and indexes a lexicon file."""
        try:
            file_path = os.path.join(self.lexicon_dir, filename)
            
            if not os.path.exists(file_path):
                return {'error': f'File not found: {filename}'}
            
            words = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    words.append(line.strip())
            
            return {
                'lexicon': filename,
                'words_loaded': len(words),
                'limit': limit,
                'words': words[:100],  # Return first 100 for preview
                'status': 'loaded'
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def build_index(self, filenames: List[str] = None) -> Dict[str, Any]:
        """Builds a master index of all lexicons."""
        try:
            if filenames is None:
                # Index all .cat files
                filenames = [f for f in os.listdir(self.lexicon_dir) if f.endswith('.cat')]
            
            master_index = defaultdict(list)
            total_entries = 0
            
            for filename in filenames:
                file_path = os.path.join(self.lexicon_dir, filename)
                
                if not os.path.exists(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            word = line.strip().lower()
                            if word:
                                master_index[filename].append(word)
                                total_entries += 1
                except Exception as e:
                    continue
            
            return {
                'indexed_files': len(filenames),
                'total_entries': total_entries,
                'files': dict(master_index),
                'status': 'indexed'
            }
        
        except Exception as e:
            return {'error': str(e)}


class SignalAggregator:
    """Aggregates signals from multiple sources."""
    
    @staticmethod
    def aggregate_sentiment_signals(days: int = 30) -> Dict[str, Any]:
        """Aggregates sentiment signals over time."""
        try:
            compiled_signals_path = os.path.join(STORAGE_DIR, 'compiled_signals.json')
            
            if os.path.exists(compiled_signals_path):
                with open(compiled_signals_path, 'r') as f:
                    signals = json.load(f)
            else:
                signals = {}
            
            # Aggregate statistics
            aggregated = {
                'total_signals': len(signals),
                'signal_categories': defaultdict(int),
                'high_intensity_signals': [],
                'temporal_coverage': f'{days} days',
                'aggregated_at': datetime.now().isoformat()
            }
            
            # Categorize signals
            for signal_key, signal_val in signals.items():
                if isinstance(signal_val, (int, float)):
                    aggregated['signal_categories']['numeric'] += 1
                    if abs(signal_val) > 2.0:
                        aggregated['high_intensity_signals'].append({
                            'signal': signal_key,
                            'intensity': signal_val
                        })
                elif isinstance(signal_val, str):
                    aggregated['signal_categories']['text'] += 1
            
            return aggregated
        
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def merge_multi_source_data(sources: List[str]) -> Dict[str, Any]:
        """Merges data from multiple source files."""
        try:
            merged_data = {
                'sources': sources,
                'entries': [],
                'merge_timestamp': datetime.now().isoformat(),
                'total_entries': 0
            }
            
            for source in sources:
                source_path = os.path.join(STORAGE_DIR, source)
                
                if os.path.exists(source_path) and source.endswith('.json'):
                    try:
                        with open(source_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                merged_data['entries'].append(data)
                            elif isinstance(data, list):
                                merged_data['entries'].extend(data)
                            merged_data['total_entries'] += 1
                    except:
                        pass
            
            return merged_data
        
        except Exception as e:
            return {'error': str(e)}


class BatchCompressor:
    """Performs batch semantic compression."""
    
    @staticmethod
    def compress_batch(json_files: List[str], output_file: str = "") -> Dict[str, Any]:
        """Compresses multiple JSON files."""
        try:
            compressed_data = {
                'input_files': len(json_files),
                'compressed_entries': [],
                'compression_stats': {
                    'original_size': 0,
                    'compressed_size': 0,
                    'compression_ratio': 0.0
                },
                'timestamp': datetime.now().isoformat()
            }
            
            for file in json_files:
                file_path = os.path.join(STORAGE_DIR, file)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        original_size = len(json.dumps(data))
                        
                        # Simple compression: key extraction
                        if isinstance(data, dict):
                            compressed = {k: v for k, v in list(data.items())[:10]}
                        else:
                            compressed = data[:10] if isinstance(data, list) else data
                        
                        compressed_size = len(json.dumps(compressed))
                        
                        compressed_data['compressed_entries'].append({
                            'source': file,
                            'original_size': original_size,
                            'compressed_size': compressed_size,
                            'ratio': original_size / (compressed_size + 1)
                        })
                        
                        compressed_data['compression_stats']['original_size'] += original_size
                        compressed_data['compression_stats']['compressed_size'] += compressed_size
                    
                    except Exception as e:
                        continue
            
            # Calculate overall ratio
            total_original = compressed_data['compression_stats']['original_size']
            total_compressed = compressed_data['compression_stats']['compressed_size']
            if total_compressed > 0:
                compressed_data['compression_stats']['compression_ratio'] = total_original / total_compressed
            
            # Write output if specified
            if output_file:
                output_path = os.path.join(STORAGE_DIR, output_file)
                with open(output_path, 'w') as f:
                    json.dump(compressed_data, f, indent=2)
                compressed_data['output_file'] = output_file
            
            return compressed_data
        
        except Exception as e:
            return {'error': str(e)}


@mcp.tool()
def list_available_lexicons() -> str:
    """Lists all available lexicon files in the lexicons directory."""
    try:
        processor = LexiconProcessor(LEXICON_DIR)
        result = processor.list_lexicons()
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def load_lexicon_file(filename: str, limit: int = 1000) -> str:
    """
    Loads a lexicon file and returns indexed words.
    Use for analyzing semantic/moral foundation vocabularies.
    """
    try:
        processor = LexiconProcessor(LEXICON_DIR)
        result = processor.load_lexicon(filename, limit)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def build_lexicon_index(filenames: str = "") -> str:
    """
    Builds master index of lexicon files.
    Filenames should be comma-separated or leave empty to index all .cat files.
    """
    try:
        file_list = [f.strip() for f in filenames.split(',')] if filenames else None
        processor = LexiconProcessor(LEXICON_DIR)
        result = processor.build_index(file_list)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def aggregate_sentiment_signals(days: int = 30) -> str:
    """
    Aggregates sentiment signals from compiled_signals.json.
    Identifies high-intensity signals and patterns.
    """
    try:
        result = SignalAggregator.aggregate_sentiment_signals(days)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def merge_multi_source_data(sources_json: str) -> str:
    """
    Merges data from multiple JSON files in storage directory.
    Input: JSON array of filenames like ["file1.json", "file2.json"]
    """
    try:
        sources = json.loads(sources_json) if isinstance(sources_json, str) else sources_json
        result = SignalAggregator.merge_multi_source_data(sources)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def batch_semantic_compression(files_json: str, output_file: str = "") -> str:
    """
    Performs batch semantic compression on multiple files.
    Input: JSON array of filenames
    Output: Compression statistics and optionally saves compressed output.
    """
    try:
        files = json.loads(files_json) if isinstance(files_json, str) else files_json
        result = BatchCompressor.compress_batch(files, output_file)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
