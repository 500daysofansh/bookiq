"""
BookIQ AI Service
Handles all AI operations:
- OpenRouter LLM integration
- Embedding generation (simple TF-IDF based, no heavy ML libs needed)
- RAG pipeline
- AI insight generation (summary, sentiment, genre)
- Book recommendations
"""
import os
import re
import json
import math
import hashlib
import logging
from typing import List, Dict, Tuple, Optional
from collections import Counter

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# OpenRouter LLM Client
# ─────────────────────────────────────────────

def call_openrouter(
    prompt: str,
    system: str = "You are a helpful book assistant.",
    max_tokens: int = 800,
    cache_key: str = None
) -> str:
    """
    Calls OpenRouter API.
    Caches responses to avoid repeated API calls (bonus feature).
    """
    # Check cache first
    if cache_key:
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache HIT for key: {cache_key}")
            return cached

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "BookIQ Platform",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        result = data["choices"][0]["message"]["content"].strip()

        # Cache the result
        if cache_key:
            cache.set(cache_key, result, settings.CACHE_TTL)

        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API error: {e}")
        raise RuntimeError(f"AI service unavailable: {str(e)}")


# ─────────────────────────────────────────────
# Simple TF-IDF Embedding (no heavy ML needed)
# ─────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """Simple word tokenizer"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return [w for w in text.split() if len(w) > 2]


def build_tfidf_vector(text: str, vocab: List[str]) -> List[float]:
    """Build a TF-IDF-like vector for a text given a vocabulary"""
    tokens = tokenize(text)
    tf = Counter(tokens)
    total = max(len(tokens), 1)
    vec = []
    for word in vocab:
        tf_val = tf.get(word, 0) / total
        vec.append(tf_val)
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Cosine similarity between two vectors"""
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


# ─────────────────────────────────────────────
# In-Memory Vector Store (ChromaDB-style)
# ─────────────────────────────────────────────

class SimpleVectorStore:
    """
    Lightweight in-memory vector store.
    Falls back gracefully if ChromaDB not available.
    Stores chunk embeddings for similarity search.
    """
    def __init__(self):
        self.chunks: List[Dict] = []   # [{id, text, book_id, book_title, metadata}]
        self.vocab: List[str] = []
        self.vectors: List[List[float]] = []
        self._vocab_built = False

    def _rebuild_vocab(self):
        """Rebuild vocabulary from all chunks"""
        all_tokens = []
        for chunk in self.chunks:
            all_tokens.extend(tokenize(chunk['text']))
        # Top 500 most common words as vocabulary
        counter = Counter(all_tokens)
        self.vocab = [w for w, _ in counter.most_common(500)]
        # Rebuild all vectors
        self.vectors = [build_tfidf_vector(c['text'], self.vocab) for c in self.chunks]
        self._vocab_built = True

    def add_chunks(self, chunks: List[Dict]):
        """Add chunks to the store"""
        for chunk in chunks:
            # Avoid duplicates
            if not any(c['id'] == chunk['id'] for c in self.chunks):
                self.chunks.append(chunk)
        self._vocab_built = False  # Need to rebuild

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find most similar chunks to query"""
        if not self.chunks:
            return []
        if not self._vocab_built:
            self._rebuild_vocab()

        q_vec = build_tfidf_vector(query, self.vocab)
        scores = [(cosine_similarity(q_vec, v), i) for i, v in enumerate(self.vectors)]
        scores.sort(reverse=True, key=lambda x: x[0])

        results = []
        for score, idx in scores[:top_k]:
            if score > 0.01:  # Minimum relevance threshold
                result = dict(self.chunks[idx])
                result['score'] = score
                results.append(result)
        return results

    def clear_book(self, book_id: int):
        """Remove all chunks for a book"""
        self.chunks = [c for c in self.chunks if c.get('book_id') != book_id]
        self._vocab_built = False


# Global vector store instance
_vector_store = SimpleVectorStore()


def get_vector_store() -> SimpleVectorStore:
    return _vector_store


# ─────────────────────────────────────────────
# Text Chunking
# ─────────────────────────────────────────────

def chunk_text(text: str, book_id: int, book_title: str, chunk_size: int = 300, overlap: int = 50) -> List[Dict]:
    """
    Smart chunking with overlapping windows.
    Splits on sentences where possible (semantic chunking).
    """
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_idx = 0

    for sentence in sentences:
        words = sentence.split()
        if current_size + len(words) > chunk_size and current_chunk:
            # Save current chunk
            chunk_text_content = ' '.join(current_chunk)
            chunk_id = f"book_{book_id}_chunk_{chunk_idx}"
            chunks.append({
                'id': chunk_id,
                'text': chunk_text_content,
                'book_id': book_id,
                'book_title': book_title,
                'chunk_index': chunk_idx,
            })
            chunk_idx += 1
            # Overlap: keep last 'overlap' words
            overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk[:]
            current_chunk = overlap_words + words
            current_size = len(current_chunk)
        else:
            current_chunk.extend(words)
            current_size += len(words)

    # Add last chunk
    if current_chunk:
        chunk_text_content = ' '.join(current_chunk)
        chunk_id = f"book_{book_id}_chunk_{chunk_idx}"
        chunks.append({
            'id': chunk_id,
            'text': chunk_text_content,
            'book_id': book_id,
            'book_title': book_title,
            'chunk_index': chunk_idx,
        })

    return chunks


# ─────────────────────────────────────────────
# AI Insight Generation
# ─────────────────────────────────────────────

def generate_summary(title: str, author: str, description: str) -> str:
    """Generate a concise book summary"""
    cache_key = f"summary_{hashlib.md5(title.encode()).hexdigest()}"
    prompt = f"""Book: "{title}" by {author}

Description: {description[:1000] if description else 'No description available.'}

Write a concise 2-3 sentence summary of this book that captures its essence, themes, and appeal."""
    return call_openrouter(prompt, cache_key=cache_key, max_tokens=200)


def classify_genre(title: str, description: str) -> Tuple[str, str]:
    """Predict genre and key themes from book metadata"""
    cache_key = f"genre_{hashlib.md5(title.encode()).hexdigest()}"
    prompt = f"""Book: "{title}"
Description: {description[:800] if description else 'No description.'}

Classify this book. Respond ONLY in this exact JSON format:
{{"genre": "Fiction/Non-Fiction/Mystery/Romance/Science Fiction/Fantasy/Biography/Self-Help/History/Horror/Thriller/Other", "themes": ["theme1", "theme2", "theme3"]}}"""
    
    result = call_openrouter(
        prompt,
        system="You are a book genre classifier. Always respond in valid JSON only.",
        cache_key=cache_key,
        max_tokens=150
    )
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            genre = data.get('genre', 'Fiction')
            themes = data.get('themes', [])
            return genre, json.dumps(themes)
    except (json.JSONDecodeError, AttributeError):
        pass
    return 'Fiction', '[]'


def analyze_sentiment(description: str) -> Tuple[str, float]:
    """Analyze sentiment of book description"""
    cache_key = f"sentiment_{hashlib.md5(description[:200].encode()).hexdigest()}"
    prompt = f"""Analyze the tone/sentiment of this book description:

"{description[:600]}"

Respond ONLY in JSON: {{"sentiment": "Positive/Negative/Neutral/Mixed", "score": 0.85}}
Score is 0.0 (very negative) to 1.0 (very positive)."""

    result = call_openrouter(
        prompt,
        system="You are a sentiment analyzer. Always respond in valid JSON only.",
        cache_key=cache_key,
        max_tokens=80
    )
    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get('sentiment', 'Neutral'), float(data.get('score', 0.5))
    except (json.JSONDecodeError, AttributeError, ValueError):
        pass
    return 'Neutral', 0.5


def generate_all_insights(book) -> Dict:
    """Generate all AI insights for a book"""
    summary = generate_summary(book.title, book.author, book.description)
    genre, themes = classify_genre(book.title, book.description)
    sentiment, score = analyze_sentiment(book.description)
    return {
        'summary': summary,
        'predicted_genre': genre,
        'key_themes': themes,
        'sentiment': sentiment,
        'sentiment_score': score,
    }


# ─────────────────────────────────────────────
# RAG Pipeline
# ─────────────────────────────────────────────

def index_book_for_rag(book) -> int:
    """
    Index a book into the vector store for RAG.
    Returns number of chunks created.
    """
    from .models import BookChunk

    # Build text to index: title + author + description + genre
    full_text = f"{book.title}. By {book.author}. "
    if book.description:
        full_text += book.description
    if book.genre:
        full_text += f" Genre: {book.genre}."

    # Create chunks
    chunks = chunk_text(full_text, book.id, book.title)

    # Save chunks to DB
    BookChunk.objects.filter(book=book).delete()
    db_chunks = []
    for chunk in chunks:
        db_chunks.append(BookChunk(
            book=book,
            chunk_index=chunk['chunk_index'],
            content=chunk['text'],
            chunk_id=chunk['id'],
        ))
    BookChunk.objects.bulk_create(db_chunks)

    # Add to vector store
    get_vector_store().add_chunks(chunks)

    return len(chunks)


def load_all_books_to_vector_store():
    """Load all books from DB into vector store on startup"""
    from .models import BookChunk
    chunks = BookChunk.objects.select_related('book').all()
    chunk_dicts = [
        {
            'id': c.chunk_id,
            'text': c.content,
            'book_id': c.book_id,
            'book_title': c.book.title,
            'chunk_index': c.chunk_index,
        }
        for c in chunks
    ]
    if chunk_dicts:
        get_vector_store().add_chunks(chunk_dicts)
        logger.info(f"Loaded {len(chunk_dicts)} chunks into vector store")


def rag_query(question: str) -> Dict:
    """
    Full RAG pipeline:
    1. Search vector store for relevant chunks
    2. Build context from retrieved chunks
    3. Generate answer with LLM + source citations
    """
    # Step 1: Retrieve relevant chunks
    relevant_chunks = get_vector_store().search(question, top_k=5)

    if not relevant_chunks:
        # Fallback: answer without context
        answer = call_openrouter(
            f"Question about books: {question}\n\nAnswer helpfully based on general book knowledge.",
            max_tokens=400
        )
        return {
            'answer': answer,
            'sources': [],
            'chunks_used': 0,
        }

    # Step 2: Build context
    context_parts = []
    sources = {}
    for chunk in relevant_chunks:
        book_title = chunk['book_title']
        if book_title not in sources:
            sources[book_title] = chunk['book_id']
        context_parts.append(f"[From: {book_title}]\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    # Step 3: Generate answer with citations
    system_prompt = """You are BookIQ, an intelligent book assistant. 
Answer questions using the provided book context. 
Always cite which book(s) your answer is based on using [Book Title] format.
Be helpful, specific, and concise."""

    prompt = f"""Context from book database:
{context}

Question: {question}

Answer based on the context above, citing sources with [Book Title]:"""

    # Cache key based on question
    cache_key = f"rag_{hashlib.md5(question.lower().strip().encode()).hexdigest()}"
    answer = call_openrouter(prompt, system=system_prompt, cache_key=cache_key, max_tokens=500)

    return {
        'answer': answer,
        'sources': [{'title': title, 'book_id': bid} for title, bid in sources.items()],
        'chunks_used': len(relevant_chunks),
    }


# ─────────────────────────────────────────────
# Recommendation Engine
# ─────────────────────────────────────────────

def get_recommendations(book, all_books, top_n: int = 5) -> List[Dict]:
    """
    Find similar books using:
    1. Genre match
    2. Text similarity of descriptions
    3. Rating proximity
    """
    if not all_books:
        return []

    candidates = [b for b in all_books if b.id != book.id]
    if not candidates:
        return []

    # Build book text for comparison
    book_text = f"{book.title} {book.genre} {book.description[:300]}"

    scored = []
    for candidate in candidates:
        score = 0.0
        cand_text = f"{candidate.title} {candidate.genre} {candidate.description[:300]}"

        # Genre match bonus
        if book.genre and candidate.genre:
            if book.genre.lower() == candidate.genre.lower():
                score += 0.4
            elif any(g in candidate.genre.lower() for g in book.genre.lower().split('/')):
                score += 0.2

        # Text similarity
        vocab = list(set(tokenize(book_text + ' ' + cand_text)))[:200]
        if vocab:
            v1 = build_tfidf_vector(book_text, vocab)
            v2 = build_tfidf_vector(cand_text, vocab)
            text_sim = cosine_similarity(v1, v2)
            score += text_sim * 0.5

        # Rating bonus
        if book.rating and candidate.rating:
            rating_diff = abs(book.rating - candidate.rating)
            score += max(0, (1 - rating_diff / 5)) * 0.1

        scored.append((score, candidate))

    scored.sort(reverse=True, key=lambda x: x[0])

    results = []
    for score, b in scored[:top_n]:
        results.append({
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'rating': b.rating,
            'genre': b.genre,
            'cover_image_url': b.cover_image_url,
            'book_url': b.book_url,
            'similarity_score': round(score, 3),
            'reason': f"Similar genre ({b.genre})" if b.genre == book.genre else "Similar themes and style",
        })
    return results
