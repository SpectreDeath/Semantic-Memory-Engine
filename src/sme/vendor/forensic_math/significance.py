import numpy as np
from typing import List, Dict, Tuple

def calculate_tfidf(tokenized_docs: List[List[str]]) -> Tuple[np.ndarray, List[str]]:
    """
    Lightweight, vectorized TF-IDF calculator.
    
    Args:
        tokenized_docs: A list of documents, where each document is a list of tokens.
        
    Returns:
        A tuple of (tfidf_matrix, vocabulary).
    """
    if not tokenized_docs:
        return np.array([]), []

    # 1. Build vocabulary
    vocabulary = sorted(list(set(token for doc in tokenized_docs for token in doc)))
    vocab_index = {word: i for i, word in enumerate(vocabulary)}
    num_docs = len(tokenized_docs)
    num_words = len(vocabulary)

    # 2. Calculate Term Frequency (TF)
    tf = np.zeros((num_docs, num_words))
    for i, doc in enumerate(tokenized_docs):
        if not doc:
            continue
        counts = np.zeros(num_words)
        for token in doc:
            if token in vocab_index:
                counts[vocab_index[token]] += 1
        tf[i, :] = counts / len(doc)

    # 3. Calculate Inverse Document Frequency (IDF)
    # Count how many documents contain each word
    doc_counts = np.sum(tf > 0, axis=0)
    # Use smoothing (add 1) to avoid division by zero
    idf = np.log(num_docs / (doc_counts + 1e-9))

    # 4. Calculate TF-IDF
    tfidf = tf * idf

    return tfidf, vocabulary

def calculate_kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """
    Measures relative entropy (Kullback-Leibler divergence) between two distributions.
    P is the target distribution, Q is the reference (baseline) distribution.
    
    Args:
        p: Probability distribution P.
        q: Probability distribution Q.
        
    Returns:
        The KL divergence value.
    """
    # Ensure they are numpy arrays
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)

    # Normalize to ensure they are true probability distributions
    p = p / (np.sum(p) + 1e-12)
    q = q / (np.sum(q) + 1e-12)

    # Avoid zero values for log and division
    epsilon = 1e-12
    p = np.clip(p, epsilon, 1.0)
    q = np.clip(q, epsilon, 1.0)

    # KL Divergence formula: sum(P(i) * log(P(i) / Q(i)))
    return float(np.sum(p * np.log(p / q)))
