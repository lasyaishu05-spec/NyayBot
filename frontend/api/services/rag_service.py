"""
NyayBot RAG (Retrieval-Augmented Generation) Service
-----------------------------------------------------
A simple, robust, and easy-to-understand Hybrid RAG pipeline designed for legal documents.
No heavy external databases or multi-gigabyte models required.

Pipeline Flow:
1. Ingestion: Splits legal text into semantic clauses/paragraphs with metadata.
2. Retrieval:
   - BM25 Okapi: Lexical search for exact legal keywords, amounts, and dates.
   - Cosine Similarity: Semantic term-frequency search for contextual relevance.
   - Reciprocal Rank Fusion (RRF): Combines both rankings for high precision.
3. Augmentation: Injects top-K relevant clauses into LLM prompts with citations.
"""

import re
import math
from typing import List, Dict, Any, Tuple


class LegalChunker:
    """Splits legal documents into logical clauses and paragraphs."""

    @staticmethod
    def chunk(text: str, target_word_size: int = 150, overlap: int = 30) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        # Split by newlines, double-newlines, or inline numbered clauses / legal headers
        split_pattern = r'(?:\n{2,}|\n(?=[0-9]{1,2}[\.\)]|[A-Z\s]{4,}:|Clause\s+\d+|Section\s+\d+|Article\s+\d+)|(?<=[;\.\n])\s+(?=[0-9]{1,2}[\.\)]\s+|Clause\s+\d+|Section\s+\d+|WHEREAS\b|NOW THIS DEED|IN WITNESS WHEREOF))'
        raw_sections = [s.strip() for s in re.split(split_pattern, text) if s.strip()]

        if not raw_sections:
            raw_sections = [text.strip()]

        chunks = []
        chunk_id = 1

        for sec in raw_sections:
            words = sec.split()
            title_match = re.match(r'^([^\n\.;]{3,65})', sec)
            title = title_match.group(1).strip() if title_match else f"Clause {chunk_id}"

            if len(words) <= target_word_size + 50:
                chunks.append({
                    "id": chunk_id,
                    "title": title,
                    "text": sec
                })
                chunk_id += 1
            else:
                # Split along sentence boundaries instead of arbitrary word breaks
                sentences = re.split(r'(?<=[.!?])\s+', sec)
                curr_sub = []
                curr_len = 0
                for s in sentences:
                    s_words = len(s.split())
                    if curr_len + s_words > target_word_size and curr_sub:
                        sub_text = " ".join(curr_sub)
                        chunks.append({
                            "id": chunk_id,
                            "title": title,
                            "text": sub_text
                        })
                        chunk_id += 1
                        curr_sub = [s]
                        curr_len = s_words
                    else:
                        curr_sub.append(s)
                        curr_len += s_words

                if curr_sub:
                    sub_text = " ".join(curr_sub)
                    chunks.append({
                        "id": chunk_id,
                        "title": title,
                        "text": sub_text
                    })
                    chunk_id += 1

        return chunks


def _stem_word(w: str) -> str:
    for suffix in ('ments', 'ment', 'ings', 'ing', 'able', 'ed', 'es', 's'):
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            return w[:-len(suffix)]
    return w


class BM25Retriever:
    """
    Lightweight BM25 Okapi retriever for exact keyword and number matching.
    Guarantees finding exact legal terms like 'Clause 4', '₹25,000', or '30 days'.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.idf: Dict[str, float] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Lowercase, stem, and split on non-alphanumeric (preserves numbers and words)
        tokens = re.findall(r'\b[a-zA-Z0-9_₹]+\b', text.lower())
        return [_stem_word(t) for t in tokens]

    def fit(self, documents: List[str]):
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.doc_lengths = [len(doc) for doc in self.corpus]
        total_docs = len(self.corpus)
        self.avg_doc_len = sum(self.doc_lengths) / max(total_docs, 1)

        # Calculate Document Frequency (DF) for each term
        df: Dict[str, int] = {}
        for doc in self.corpus:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1

        # Calculate Inverse Document Frequency (IDF)
        self.idf = {}
        for term, freq in df.items():
            # Standard Lucene/Okapi smoothed IDF formula
            self.idf[term] = math.log(1 + (total_docs - freq + 0.5) / (freq + 0.5))

    def score(self, query: str) -> List[float]:
        query_terms = self.tokenize(query)
        scores = [0.0] * len(self.corpus)

        for i, doc in enumerate(self.corpus):
            doc_len = self.doc_lengths[i]
            if doc_len == 0:
                continue

            # Calculate term frequencies in current doc
            tf: Dict[str, int] = {}
            for t in doc:
                tf[t] = tf.get(t, 0) + 1

            doc_score = 0.0
            for term in query_terms:
                if term in tf:
                    term_idf = self.idf.get(term, 0.0)
                    term_tf = tf[term]
                    numerator = term_tf * (self.k1 + 1)
                    denominator = term_tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                    doc_score += term_idf * (numerator / denominator)

            scores[i] = doc_score

        return scores


class TFIDFVectorRetriever:
    """
    Lightweight Cosine Similarity Retriever.
    Provides semantic vector-like matching using sublinear TF-IDF representation.
    """

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: List[float] = []
        self.doc_vectors: List[Dict[int, float]] = []
        self.doc_norms: List[float] = []

    @staticmethod
    def tokenize(text: str) -> List[str]:
        tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower())
        return [_stem_word(t) for t in tokens]

    def fit(self, documents: List[str]):
        tokenized_docs = [self.tokenize(doc) for doc in documents]
        num_docs = len(documents)

        # Build vocabulary
        vocab_set = set()
        for doc in tokenized_docs:
            vocab_set.update(doc)
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(vocab_set))}

        # Calculate Document Frequency
        df = [0] * len(self.vocabulary)
        for doc in tokenized_docs:
            for term in set(doc):
                df[self.vocabulary[term]] += 1

        # Smooth IDF
        self.idf = [math.log((num_docs + 1) / (freq + 1)) + 1.0 for freq in df]

        # Build sparse document vectors and compute norms
        self.doc_vectors = []
        self.doc_norms = []
        for doc in tokenized_docs:
            vec: Dict[int, float] = {}
            for term in doc:
                idx = self.vocabulary[term]
                vec[idx] = vec.get(idx, 0.0) + 1.0

            # Apply sublinear TF: 1 + log(tf)
            for idx in vec:
                vec[idx] = (1.0 + math.log(vec[idx])) * self.idf[idx]

            norm = math.sqrt(sum(val * val for val in vec.values()))
            self.doc_vectors.append(vec)
            self.doc_norms.append(norm if norm > 0 else 1.0)

    def score(self, query: str) -> List[float]:
        query_terms = self.tokenize(query)
        query_vec: Dict[int, float] = {}
        for term in query_terms:
            if term in self.vocabulary:
                idx = self.vocabulary[term]
                query_vec[idx] = query_vec.get(idx, 0.0) + 1.0

        for idx in query_vec:
            query_vec[idx] = (1.0 + math.log(query_vec[idx])) * self.idf[idx]

        query_norm = math.sqrt(sum(val * val for val in query_vec.values()))
        if query_norm == 0:
            return [0.0] * len(self.doc_vectors)

        scores = [0.0] * len(self.doc_vectors)
        for i, doc_vec in enumerate(self.doc_vectors):
            dot_product = sum(query_vec[idx] * doc_vec[idx] for idx in query_vec if idx in doc_vec)
            scores[i] = dot_product / (query_norm * self.doc_norms[i])

        return scores


class SimpleLegalRAG:
    """
    Unified, easy-to-understand Hybrid RAG pipeline for NyayBot.
    Combines BM25 Lexical + Vector Cosine with Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, target_word_size: int = 150, overlap: int = 30):
        self.target_word_size = target_word_size
        self.overlap = overlap

    def index_and_retrieve(
        self,
        document_text: str,
        query: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Takes raw document text and a user query.
        Returns top-K relevant chunks with citations and fused scores.
        """
        # 1. Chunk document
        chunks = LegalChunker.chunk(document_text, self.target_word_size, self.overlap)
        if not chunks:
            return []

        if len(chunks) <= top_k:
            # If document is tiny, return all chunks directly
            for i, ch in enumerate(chunks):
                ch["score"] = 1.0
                ch["rank"] = i + 1
            return chunks

        doc_texts = [ch["text"] for ch in chunks]

        # 2. BM25 Lexical Search
        bm25 = BM25Retriever()
        bm25.fit(doc_texts)
        bm25_scores = bm25.score(query)

        # 3. Dense / Semantic Vector Search
        vec_search = TFIDFVectorRetriever()
        vec_search.fit(doc_texts)
        vec_scores = vec_search.score(query)

        # 4. Reciprocal Rank Fusion (RRF)
        # Sort indices by each method's score
        bm25_ranked = sorted(range(len(chunks)), key=lambda i: bm25_scores[i], reverse=True)
        vec_ranked = sorted(range(len(chunks)), key=lambda i: vec_scores[i], reverse=True)

        k_rrf = 60  # Standard RRF constant
        rrf_scores = [0.0] * len(chunks)

        for rank, idx in enumerate(bm25_ranked):
            if bm25_scores[idx] > 0:
                rrf_scores[idx] += 1.0 / (k_rrf + rank + 1)

        for rank, idx in enumerate(vec_ranked):
            if vec_scores[idx] > 0:
                rrf_scores[idx] += 1.0 / (k_rrf + rank + 1)

        # Combine results
        final_ranked_indices = sorted(range(len(chunks)), key=lambda i: rrf_scores[i], reverse=True)

        results = []
        for rank, idx in enumerate(final_ranked_indices[:top_k]):
            chunk_copy = dict(chunks[idx])
            chunk_copy["score"] = round(rrf_scores[idx], 4)
            chunk_copy["rank"] = rank + 1
            results.append(chunk_copy)

        return results

    def build_augmented_context(
        self,
        document_text: str,
        query: str,
        top_k: int = 4
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Builds the context string formatted with citations ready for LLM prompt injection.
        """
        retrieved_chunks = self.index_and_retrieve(document_text, query, top_k)
        if not retrieved_chunks:
            return document_text[:4000], []

        context_lines = []
        for ch in retrieved_chunks:
            context_lines.append(
                f"[Source: Chunk {ch['id']} - {ch['title']}]\n{ch['text']}"
            )

        augmented_context = "\n\n---\n\n".join(context_lines)
        return augmented_context, retrieved_chunks


# Global singleton instance for clean reuse
rag_pipeline = SimpleLegalRAG()
