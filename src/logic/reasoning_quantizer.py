"""
Distills raw assertions (e.g. CSV) into HDF5 knowledge_core (entities/relationships).
Implements actual CSV parsing with support for ConceptNet-style assertions and custom formats.
"""
import h5py
import numpy as np
import os
import csv
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ReasoningQuantizer:
    def __init__(self, h5_path: str = None):
        if h5_path is None:
            self.h5_path = os.getenv("KNOWLEDGE_CORE_PATH", "data/knowledge_core.h5")
        else:
            self.h5_path = h5_path
        
    def distill_assertions(self, csv_path: str, format_type: str = "conceptnet") -> Dict[str, Any]:
        """
        Processes raw CSV into high-performance HDF5 format.
        
        Args:
            csv_path: Path to the CSV file containing assertions
            format_type: Type of CSV format ("conceptnet", "custom", "auto")
            
        Returns:
            Dict with statistics about the distillation process
        """
        if not os.path.exists("data"):
            os.makedirs("data")
            
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
        # Determine format and parse accordingly
        if format_type == "auto":
            format_type = self._detect_format(csv_path)
            logger.info(f"Auto-detected format: {format_type}")
            
        # Parse CSV and extract entities/relationships
        entities, relationships = self._parse_csv(csv_path, format_type)
        
        # Create HDF5 structure
        stats = self._create_hdf5_structure(entities, relationships)
        
        logger.info(f"✨ Distilled {csv_path} to {self.h5_path}")
        logger.info(f"   Entities: {stats['entity_count']:,}")
        logger.info(f"   Relationships: {stats['relationship_count']:,}")
        logger.info(f"   File size: {stats['file_size_mb']:.2f} MB")
        
        return stats
    
    def _detect_format(self, csv_path: str) -> str:
        """Auto-detect CSV format by examining headers and sample data."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                reader = csv.reader(f, dialect)
                
                # Read header
                header = next(reader, [])
                header_str = '|'.join(header).lower()
                
                # Check for ConceptNet format
                if 'uri' in header_str and ('relation' in header_str or 'rel' in header_str):
                    return "conceptnet"
                elif len(header) >= 3 and all(h in header_str for h in ['subject', 'predicate', 'object']):
                    return "custom"
                else:
                    return "custom"
        except Exception as e:
            logger.warning(f"Format detection failed: {e}. Defaulting to custom format.")
            return "custom"
    
    def _parse_csv(self, csv_path: str, format_type: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """Parse CSV file and extract entities and relationships."""
        entities = {}
        relationships = []
        entity_counter = 0
        rel_counter = 0
        
        logger.info(f"Parsing CSV in {format_type} format...")
        
        if format_type == "conceptnet":
            entities, relationships = self._parse_conceptnet_csv(csv_path)
        else:
            entities, relationships = self._parse_custom_csv(csv_path)
            
        return entities, relationships
    
    def _parse_conceptnet_csv(self, csv_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """Parse ConceptNet-style CSV format."""
        entities = {}
        relationships = []
        entity_counter = 0
        rel_counter = 0
        
        # ConceptNet columns: uri, relation, start, end, dataset, sources, surfaceText, weight
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Extract entities
                    start_uri = row.get('start', '').strip()
                    end_uri = row.get('end', '').strip()
                    relation = row.get('relation', '').strip()
                    
                    if not start_uri or not end_uri or not relation:
                        continue
                    
                    # Add entities if not already present
                    if start_uri not in entities:
                        entities[start_uri] = entity_counter
                        entity_counter += 1
                    if end_uri not in entities:
                        entities[end_uri] = entity_counter
                        entity_counter += 1
                    
                    # Create relationship
                    weight = float(row.get('weight', 1.0))
                    dataset = row.get('dataset', 'unknown')
                    surface_text = row.get('surfaceText', '')
                    
                    relationship = {
                        'id': rel_counter,
                        'subject_id': entities[start_uri],
                        'object_id': entities[end_uri],
                        'relation': relation,
                        'weight': weight,
                        'dataset': dataset,
                        'surface_text': surface_text,
                        'source_uri': row.get('uri', ''),
                        'sources': row.get('sources', '')
                    }
                    relationships.append(relationship)
                    rel_counter += 1
                    
                    # Progress logging
                    if rel_counter % 100000 == 0:
                        logger.info(f"Processed {rel_counter:,} relationships...")
                        
        except Exception as e:
            logger.error(f"Error parsing ConceptNet CSV: {e}")
            raise
            
        return entities, relationships
    
    def _parse_custom_csv(self, csv_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """Parse custom CSV format with subject, predicate, object columns."""
        entities = {}
        relationships = []
        entity_counter = 0
        rel_counter = 0
        
        try:
            # Use pandas for efficient parsing
            df = pd.read_csv(csv_path)
            
            # Normalize column names
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Look for standard columns
            subject_col = None
            predicate_col = None
            object_col = None
            
            for col in df.columns:
                if any(term in col for term in ['subject', 'subj', 'source', 'from']):
                    subject_col = col
                elif any(term in col for term in ['predicate', 'pred', 'relation', 'rel', 'verb']):
                    predicate_col = col
                elif any(term in col for term in ['object', 'obj', 'target', 'to']):
                    object_col = col
            
            if not all([subject_col, predicate_col, object_col]):
                raise ValueError("CSV must contain subject, predicate, and object columns")
            
            # Process rows
            for idx, row in df.iterrows():
                subject = str(row[subject_col]).strip()
                predicate = str(row[predicate_col]).strip()
                obj = str(row[object_col]).strip()
                
                if not subject or not predicate or not obj:
                    continue
                
                # Add entities if not already present
                if subject not in entities:
                    entities[subject] = entity_counter
                    entity_counter += 1
                if obj not in entities:
                    entities[obj] = entity_counter
                    entity_counter += 1
                
                # Create relationship
                relationship = {
                    'id': rel_counter,
                    'subject_id': entities[subject],
                    'object_id': entities[obj],
                    'relation': predicate,
                    'weight': 1.0,  # Default weight for custom format
                    'dataset': 'custom',
                    'surface_text': '',
                    'source_uri': '',
                    'sources': ''
                }
                relationships.append(relationship)
                rel_counter += 1
                
                # Progress logging
                if rel_counter % 100000 == 0:
                    logger.info(f"Processed {rel_counter:,} relationships...")
                    
        except Exception as e:
            logger.error(f"Error parsing custom CSV: {e}")
            raise
            
        return entities, relationships
    
    def _create_hdf5_structure(self, entities: Dict[str, int], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create HDF5 structure with entities and relationships datasets."""
        start_time = pd.Timestamp.now()
        
        with h5py.File(self.h5_path, 'w') as f:
            # Create entities group and dataset
            entities_group = f.create_group("entities")
            entity_names = list(entities.keys())
            entity_ids = list(entities.values())
            
            # Store entity mapping
            entities_group.create_dataset("names", data=np.array(entity_names, dtype='S'))
            entities_group.create_dataset("ids", data=np.array(entity_ids, dtype='i4'))
            entities_group.attrs['count'] = len(entities)
            
            # Create relationships group and dataset
            relationships_group = f.create_group("relationships")
            
            if relationships:
                # Prepare relationship data arrays
                rel_ids = np.array([r['id'] for r in relationships], dtype='i8')
                subject_ids = np.array([r['subject_id'] for r in relationships], dtype='i4')
                object_ids = np.array([r['object_id'] for r in relationships], dtype='i4')
                weights = np.array([r['weight'] for r in relationships], dtype='f4')
                
                # Store string data separately for efficiency
                relations = np.array([r['relation'] for r in relationships], dtype='S')
                datasets = np.array([r['dataset'] for r in relationships], dtype='S')
                surface_texts = np.array([r['surface_text'] for r in relationships], dtype='S')
                source_uris = np.array([r['source_uri'] for r in relationships], dtype='S')
                sources = np.array([r['sources'] for r in relationships], dtype='S')
                
                # Create datasets
                relationships_group.create_dataset("ids", data=rel_ids)
                relationships_group.create_dataset("subject_ids", data=subject_ids)
                relationships_group.create_dataset("object_ids", data=object_ids)
                relationships_group.create_dataset("relations", data=relations)
                relationships_group.create_dataset("weights", data=weights)
                relationships_group.create_dataset("datasets", data=datasets)
                relationships_group.create_dataset("surface_texts", data=surface_texts)
                relationships_group.create_dataset("source_uris", data=source_uris)
                relationships_group.create_dataset("sources", data=sources)
                
                relationships_group.attrs['count'] = len(relationships)
            else:
                # Empty relationships dataset
                relationships_group.create_dataset("ids", data=np.array([], dtype='i8'))
                relationships_group.create_dataset("subject_ids", data=np.array([], dtype='i4'))
                relationships_group.create_dataset("object_ids", data=np.array([], dtype='i4'))
                relationships_group.create_dataset("relations", data=np.array([], dtype='S'))
                relationships_group.create_dataset("weights", data=np.array([], dtype='f4'))
                relationships_group.create_dataset("datasets", data=np.array([], dtype='S'))
                relationships_group.create_dataset("surface_texts", data=np.array([], dtype='S'))
                relationships_group.create_dataset("source_uris", data=np.array([], dtype='S'))
                relationships_group.create_dataset("sources", data=np.array([], dtype='S'))
                relationships_group.attrs['count'] = 0
            
            # Add metadata
            f.attrs['created_at'] = pd.Timestamp.now().isoformat()
            f.attrs['format_version'] = '1.0'
            f.attrs['entity_count'] = len(entities)
            f.attrs['relationship_count'] = len(relationships)
            
        # Calculate statistics
        file_size = os.path.getsize(self.h5_path)
        duration = (pd.Timestamp.now() - start_time).total_seconds()
        
        stats = {
            'entity_count': len(entities),
            'relationship_count': len(relationships),
            'file_size_bytes': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'processing_time_seconds': duration,
            'entities_per_second': len(entities) / duration if duration > 0 else 0,
            'relationships_per_second': len(relationships) / duration if duration > 0 else 0
        }
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current HDF5 knowledge core."""
        if not os.path.exists(self.h5_path):
            return {'error': 'Knowledge core not found'}
            
        try:
            with h5py.File(self.h5_path, 'r') as f:
                stats = {
                    'file_size_mb': os.path.getsize(self.h5_path) / (1024 * 1024),
                    'format_version': f.attrs.get('format_version', 'unknown'),
                    'created_at': f.attrs.get('created_at', 'unknown'),
                    'entity_count': f.attrs.get('entity_count', 0),
                    'relationship_count': f.attrs.get('relationship_count', 0)
                }
                
                # Additional entity statistics
                if 'entities' in f:
                    entity_group = f['entities']
                    stats['entity_storage_size'] = entity_group['names'].size * entity_group['names'].dtype.itemsize / (1024 * 1024)
                
                # Additional relationship statistics
                if 'relationships' in f:
                    rel_group = f['relationships']
                    stats['relationship_storage_size'] = sum(
                        dataset.size * dataset.dtype.itemsize 
                        for dataset in rel_group.values()
                    ) / (1024 * 1024)
                    
                return stats
        except Exception as e:
            return {'error': f'Failed to read statistics: {e}'}
