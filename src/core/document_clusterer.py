"""
Document Clustering Module
===========================

Phase 5 component for semantic document clustering and topic analysis.
Groups similar documents and extracts common themes.

Features:
- K-Means clustering
- Hierarchical clustering
- Topic extraction
- Document similarity measurement
- Cluster analysis and characterization
- Dynamic cluster number estimation
"""

import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
import math
from collections import Counter

try:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


class ClusteringAlgorithm(Enum):
    """Clustering algorithms."""
    KMEANS = "kmeans"
    HIERARCHICAL = "hierarchical"
    DENSITY_BASED = "density_based"


@dataclass
class DocumentVector:
    """TF-IDF vector representation of document."""
    doc_id: str
    text: str
    tokens: List[str]
    vector: Dict[str, float]  # word -> weight
    magnitude: float


@dataclass
class ClusterMember:
    """Document in a cluster."""
    doc_id: str
    text: str
    similarity: float  # To cluster center


@dataclass
class Cluster:
    """Document cluster."""
    cluster_id: int
    members: List[ClusterMember]
    top_terms: List[Tuple[str, float]]  # Word -> weight
    centroid: Dict[str, float]
    size: int
    cohesion: float  # Internal similarity
    separation: float  # Distance to nearest cluster


@dataclass
class ClusteringResult:
    """Complete clustering result."""
    num_clusters: int
    algorithm: ClusteringAlgorithm
    clusters: List[Cluster]
    silhouette_score: float
    topic_labels: Dict[int, str]  # Cluster -> topic label
    document_assignments: Dict[str, int]  # Doc -> cluster
    

class DocumentClusterer:
    """Document clustering and topic analysis engine."""
    
    def __init__(self):
        """Initialize clusterer."""
        self.has_nltk = NLTK_AVAILABLE
        if self.has_nltk:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                self.stop_words = self._get_basic_stopwords()
        else:
            self.stop_words = self._get_basic_stopwords()
    
    def cluster(self, documents: List[str], num_clusters: Optional[int] = None,
               algorithm: ClusteringAlgorithm = ClusteringAlgorithm.KMEANS) -> ClusteringResult:
        """
        Cluster documents into groups.
        
        Args:
            documents: List of documents to cluster
            num_clusters: Number of clusters (auto-estimate if None)
            algorithm: Clustering algorithm to use
        """
        if len(documents) < 2:
            return self._create_single_cluster_result(documents, algorithm)
        
        # Estimate optimal clusters if not specified
        if num_clusters is None:
            num_clusters = self._estimate_optimal_clusters(documents)
        
        num_clusters = max(1, min(num_clusters, len(documents)))
        
        # Build document vectors
        doc_vectors = self._vectorize_documents(documents)
        
        if algorithm == ClusteringAlgorithm.KMEANS:
            clusters = self._kmeans_cluster(doc_vectors, num_clusters)
        elif algorithm == ClusteringAlgorithm.HIERARCHICAL:
            clusters = self._hierarchical_cluster(doc_vectors, num_clusters)
        else:
            clusters = self._density_cluster(doc_vectors)
        
        # Characterize clusters
        self._characterize_clusters(clusters)
        
        # Calculate quality metrics
        silhouette = self._calculate_silhouette_score(clusters, doc_vectors)
        
        # Generate topic labels
        topic_labels = self._generate_topic_labels(clusters)
        
        # Build document assignments
        doc_assignments = {v.doc_id: -1 for v in doc_vectors}
        for cluster in clusters:
            for member in cluster.members:
                doc_assignments[member.doc_id] = cluster.cluster_id
        
        return ClusteringResult(
            num_clusters=len(clusters),
            algorithm=algorithm,
            clusters=clusters,
            silhouette_score=silhouette,
            topic_labels=topic_labels,
            document_assignments=doc_assignments
        )
    
    def get_similar_documents(self, target_doc: str, documents: List[str],
                             top_n: int = 5) -> List[Tuple[str, float]]:
        """Find documents similar to target."""
        target_vector = self._vectorize_document(target_doc)
        similarities = []
        
        for doc in documents:
            if doc == target_doc:
                continue
            
            doc_vector = self._vectorize_document(doc)
            sim = self._cosine_similarity(target_vector, doc_vector)
            similarities.append((doc, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def extract_topic_keywords(self, cluster: Cluster, top_n: int = 10) -> List[str]:
        """Extract keywords for cluster topic."""
        return [word for word, _ in cluster.top_terms[:top_n]]
    
    def merge_clusters(self, clusters: List[Cluster], threshold: float = 0.8) -> List[Cluster]:
        """Merge similar clusters."""
        merged = []
        used = set()
        
        for i, cluster1 in enumerate(clusters):
            if i in used:
                continue
            
            new_cluster = Cluster(
                cluster_id=cluster1.cluster_id,
                members=list(cluster1.members),
                top_terms=list(cluster1.top_terms),
                centroid=dict(cluster1.centroid),
                size=cluster1.size,
                cohesion=cluster1.cohesion,
                separation=cluster1.separation
            )
            
            # Find clusters to merge
            for j, cluster2 in enumerate(clusters[i+1:], start=i+1):
                if j in used:
                    continue
                
                similarity = self._calculate_cluster_similarity(cluster1, cluster2)
                if similarity >= threshold:
                    new_cluster.members.extend(cluster2.members)
                    new_cluster.size += cluster2.size
                    used.add(j)
            
            merged.append(new_cluster)
        
        return merged
    
    def _estimate_optimal_clusters(self, documents: List[str]) -> int:
        """Estimate optimal number of clusters using elbow method."""
        # Simple heuristic: sqrt(n/2)
        n = len(documents)
        estimated = max(1, int(math.sqrt(n / 2)))
        return min(estimated, n)
    
    def _vectorize_documents(self, documents: List[str]) -> List[DocumentVector]:
        """Convert documents to TF-IDF vectors."""
        # Tokenize all documents
        all_tokens = []
        doc_token_lists = []
        
        for doc in documents:
            tokens = self._tokenize(doc.lower())
            tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
            doc_token_lists.append(tokens)
            all_tokens.extend(tokens)
        
        # Calculate document frequencies
        df = Counter()
        for tokens in doc_token_lists:
            df.update(set(tokens))
        
        # Calculate TF-IDF
        num_docs = len(documents)
        vectors = []
        
        for doc_id, tokens in enumerate(doc_token_lists):
            tf = Counter(tokens)
            vector = {}
            magnitude = 0.0
            
            for term, count in tf.items():
                # TF-IDF calculation
                tf_val = count / max(len(tokens), 1)
                idf_val = math.log(num_docs / max(df[term], 1))
                tfidf = tf_val * idf_val
                
                vector[term] = tfidf
                magnitude += tfidf ** 2
            
            magnitude = math.sqrt(magnitude)
            
            vectors.append(DocumentVector(
                doc_id=str(doc_id),
                text=documents[doc_id],
                tokens=tokens,
                vector=vector,
                magnitude=max(magnitude, 0.0001)
            ))
        
        return vectors
    
    def _vectorize_document(self, document: str) -> Dict[str, float]:
        """Vectorize single document."""
        tokens = self._tokenize(document.lower())
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        
        tf = Counter(tokens)
        vector = {}
        
        for term, count in tf.items():
            vector[term] = count / max(len(tokens), 1)
        
        return vector
    
    def _kmeans_cluster(self, doc_vectors: List[DocumentVector],
                       k: int) -> List[Cluster]:
        """K-Means clustering algorithm."""
        # Initialize centroids randomly
        import random
        centroid_indices = random.sample(range(len(doc_vectors)), k)
        centroids = [doc_vectors[i].vector for i in centroid_indices]
        
        assignments = [-1] * len(doc_vectors)
        converged = False
        iterations = 0
        max_iterations = 10
        
        while not converged and iterations < max_iterations:
            # Assign documents to nearest centroid
            new_assignments = []
            for vec in doc_vectors:
                best_centroid = 0
                best_distance = float('inf')
                
                for c_idx, centroid in enumerate(centroids):
                    distance = self._vector_distance(vec.vector, centroid)
                    if distance < best_distance:
                        best_distance = distance
                        best_centroid = c_idx
                
                new_assignments.append(best_centroid)
            
            # Check convergence
            if new_assignments == assignments:
                converged = True
            
            assignments = new_assignments
            
            # Update centroids
            new_centroids = []
            for c_idx in range(k):
                cluster_vectors = [doc_vectors[i].vector for i in range(len(doc_vectors))
                                 if assignments[i] == c_idx]
                
                if cluster_vectors:
                    centroid = self._average_vectors(cluster_vectors)
                else:
                    centroid = centroids[c_idx]
                
                new_centroids.append(centroid)
            
            centroids = new_centroids
            iterations += 1
        
        # Create cluster objects
        clusters = []
        for c_idx in range(k):
            members = []
            for doc_idx, assignment in enumerate(assignments):
                if assignment == c_idx:
                    doc_vec = doc_vectors[doc_idx]
                    members.append(ClusterMember(
                        doc_id=doc_vec.doc_id,
                        text=doc_vec.text,
                        similarity=1.0 - self._vector_distance(doc_vec.vector, centroids[c_idx])
                    ))
            
            top_terms = self._extract_top_terms(centroids[c_idx], 10)
            
            clusters.append(Cluster(
                cluster_id=c_idx,
                members=members,
                top_terms=top_terms,
                centroid=centroids[c_idx],
                size=len(members),
                cohesion=0.0,
                separation=0.0
            ))
        
        return clusters
    
    def _hierarchical_cluster(self, doc_vectors: List[DocumentVector],
                             k: int) -> List[Cluster]:
        """Simplified hierarchical clustering."""
        # Start with each document as its own cluster
        clusters = [[doc_vec] for doc_vec in doc_vectors]
        
        # Merge until we have k clusters
        while len(clusters) > k:
            # Find most similar pair
            best_i, best_j = 0, 1
            best_distance = float('inf')
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    distance = self._cluster_distance(clusters[i], clusters[j])
                    if distance < best_distance:
                        best_distance = distance
                        best_i, best_j = i, j
            
            # Merge clusters
            clusters[best_i].extend(clusters[best_j])
            clusters.pop(best_j)
        
        # Create cluster objects
        result_clusters = []
        for c_idx, cluster_docs in enumerate(clusters):
            centroid = self._calculate_centroid(cluster_docs)
            members = [ClusterMember(d.doc_id, d.text, 0.8) for d in cluster_docs]
            top_terms = self._extract_top_terms(centroid, 10)
            
            result_clusters.append(Cluster(
                cluster_id=c_idx,
                members=members,
                top_terms=top_terms,
                centroid=centroid,
                size=len(members),
                cohesion=0.0,
                separation=0.0
            ))
        
        return result_clusters
    
    def _density_cluster(self, doc_vectors: List[DocumentVector]) -> List[Cluster]:
        """Simplified density-based clustering."""
        # For simplicity, fall back to k-means with auto k
        k = self._estimate_optimal_clusters([v.text for v in doc_vectors])
        return self._kmeans_cluster(doc_vectors, k)
    
    def _characterize_clusters(self, clusters: List[Cluster]):
        """Calculate cluster characteristics."""
        for cluster in clusters:
            if not cluster.members:
                continue
            
            # Calculate cohesion (average internal similarity)
            similarities = [m.similarity for m in cluster.members]
            cluster.cohesion = sum(similarities) / len(similarities) if similarities else 0.0
    
    def _calculate_silhouette_score(self, clusters: List[Cluster],
                                   doc_vectors: List[DocumentVector]) -> float:
        """Calculate silhouette score for clustering quality."""
        if len(clusters) < 2:
            return 1.0
        
        scores = []
        
        for cluster in clusters:
            for member in cluster.members:
                doc_vec = next((v for v in doc_vectors if v.doc_id == member.doc_id), None)
                if not doc_vec:
                    continue
                
                # Intra-cluster distance
                a = 1.0 - member.similarity
                
                # Inter-cluster distance (to nearest other cluster)
                b = float('inf')
                for other_cluster in clusters:
                    if other_cluster.cluster_id == cluster.cluster_id:
                        continue
                    
                    for other_member in other_cluster.members:
                        if other_member.doc_id == member.doc_id:
                            distance = 1.0 - other_member.similarity
                            b = min(b, distance)
                
                if b == float('inf'):
                    b = a
                
                # Silhouette coefficient
                silhouette = (b - a) / max(a, b) if max(a, b) > 0 else 0
                scores.append(silhouette)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_topic_labels(self, clusters: List[Cluster]) -> Dict[int, str]:
        """Generate topic labels for clusters."""
        labels = {}
        
        for cluster in clusters:
            if cluster.top_terms:
                # Use top 3 terms to create label
                top_terms = [term for term, _ in cluster.top_terms[:3]]
                label = ", ".join(top_terms)
            else:
                label = f"Cluster {cluster.cluster_id}"
            
            labels[cluster.cluster_id] = label
        
        return labels
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between vectors."""
        dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) 
                         for term in set(vec1.keys()) | set(vec2.keys()))
        
        mag1 = math.sqrt(sum(v**2 for v in vec1.values())) or 1.0
        mag2 = math.sqrt(sum(v**2 for v in vec2.values())) or 1.0
        
        return dot_product / (mag1 * mag2) if mag1 * mag2 > 0 else 0.0
    
    def _vector_distance(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate Euclidean distance between vectors."""
        distance = 0.0
        all_terms = set(vec1.keys()) | set(vec2.keys())
        
        for term in all_terms:
            diff = vec1.get(term, 0) - vec2.get(term, 0)
            distance += diff ** 2
        
        return math.sqrt(distance)
    
    def _average_vectors(self, vectors: List[Dict[str, float]]) -> Dict[str, float]:
        """Average multiple vectors."""
        if not vectors:
            return {}
        
        result = {}
        all_terms = set()
        for vec in vectors:
            all_terms.update(vec.keys())
        
        for term in all_terms:
            values = [v.get(term, 0) for v in vectors]
            result[term] = sum(values) / len(values)
        
        return result
    
    def _calculate_centroid(self, doc_vectors: List[DocumentVector]) -> Dict[str, float]:
        """Calculate centroid of documents."""
        vectors = [dv.vector for dv in doc_vectors]
        return self._average_vectors(vectors)
    
    def _cluster_distance(self, cluster1: List[DocumentVector],
                         cluster2: List[DocumentVector]) -> float:
        """Calculate distance between two clusters."""
        centroid1 = self._calculate_centroid(cluster1)
        centroid2 = self._calculate_centroid(cluster2)
        return self._vector_distance(centroid1, centroid2)
    
    def _calculate_cluster_similarity(self, cluster1: Cluster, cluster2: Cluster) -> float:
        """Calculate similarity between two clusters."""
        return 1.0 - self._vector_distance(cluster1.centroid, cluster2.centroid)
    
    def _extract_top_terms(self, vector: Dict[str, float], top_n: int) -> List[Tuple[str, float]]:
        """Extract top terms from vector."""
        sorted_terms = sorted(vector.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:top_n]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text."""
        if self.has_nltk:
            try:
                return word_tokenize(text)
            except:
                pass
        
        import re
        return re.findall(r'\b\w+\b', text.lower())
    
    def _get_basic_stopwords(self) -> set:
        """Get basic stopwords."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who'
        }
    
    def _create_single_cluster_result(self, documents: List[str],
                                     algorithm: ClusteringAlgorithm) -> ClusteringResult:
        """Create result for single cluster."""
        all_text = " ".join(documents)
        doc_vecs = self._vectorize_documents(documents)
        centroid = self._calculate_centroid(doc_vecs)
        
        members = [ClusterMember(v.doc_id, v.text, 1.0) for v in doc_vecs]
        top_terms = self._extract_top_terms(centroid, 10)
        
        cluster = Cluster(
            cluster_id=0,
            members=members,
            top_terms=top_terms,
            centroid=centroid,
            size=len(members),
            cohesion=1.0,
            separation=0.0
        )
        
        return ClusteringResult(
            num_clusters=1,
            algorithm=algorithm,
            clusters=[cluster],
            silhouette_score=0.0,
            topic_labels={0: "All Documents"},
            document_assignments={v.doc_id: 0 for v in doc_vecs}
        )
