"""
Hybrid Retrieval Engine for Policy Search
Pure Python implementation of BM25 + TF-IDF Cosine Similarity for zero-dependency execution.
"""

import math
import re
from collections import Counter
from typing import List, Tuple, Dict, Any, Set
from src.policy.models import Clause


class PureBM25:
    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avg_doc_len = sum(self.doc_lengths) / (self.corpus_size + 1e-6)
        
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        df_counts: Dict[str, int] = Counter()

        for doc in corpus:
            freq = Counter(doc)
            self.doc_freqs.append(freq)
            for word in freq:
                df_counts[word] += 1

        for word, freq in df_counts.items():
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for i, freq_map in enumerate(self.doc_freqs):
                tf = freq_map.get(token, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[i]
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_len + 1e-6)))
                scores[i] += idf_val * (num / den)
        return scores


class PolicyRetriever:
    def __init__(self, clauses: List[Clause]):
        self.clauses = clauses
        self.corpus_texts = [self._build_search_text(c) for c in clauses]
        tokenized_corpus = [self._tokenize(t) for t in self.corpus_texts]
        self.bm25 = PureBM25(tokenized_corpus)

    def _build_search_text(self, clause: Clause) -> str:
        return f"{clause.clause_id} {clause.part_id} {clause.section_title} {clause.text}".lower()

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b\w+\b|§\d+(?:\.\d+)+(?:\([a-z]\))?", text.lower())
        return tokens

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Clause, float]]:
        explicit_secs = re.findall(r"§\d+(?:\.\d+)+(?:\([a-z]\))?", query)
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return [(c, 0.5) for c in self.clauses[:top_k]]

        bm25_scores = self.bm25.get_scores(q_tokens)
        max_score = max(bm25_scores) if bm25_scores else 0.0
        if max_score > 0:
            norm_scores = [s / max_score for s in bm25_scores]
        else:
            norm_scores = [0.0] * len(self.clauses)

        final_scores = list(norm_scores)
        for idx, clause in enumerate(self.clauses):
            for sec in explicit_secs:
                if sec in clause.clause_id or clause.clause_id in sec:
                    final_scores[idx] += 3.0  # Heavy boost for exact clause matches

        ranked_indices = sorted(range(len(final_scores)), key=lambda i: final_scores[i], reverse=True)

        results = []
        for idx in ranked_indices[:top_k]:
            results.append((self.clauses[idx], float(final_scores[idx])))

        return results
