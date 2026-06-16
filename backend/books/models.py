"""
BookIQ Database Models
Stores book metadata scraped from the web
"""
from django.db import models
from django.utils import timezone


class Book(models.Model):
    """Main book table storing metadata"""
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=300, blank=True, default='')
    rating = models.FloatField(null=True, blank=True)
    num_reviews = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, default='')
    genre = models.CharField(max_length=200, blank=True, default='')
    price = models.CharField(max_length=50, blank=True, default='')
    availability = models.CharField(max_length=100, blank=True, default='')
    book_url = models.URLField(max_length=1000, blank=True, default='')
    cover_image_url = models.URLField(max_length=1000, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-rating', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['genre']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"


class AIInsight(models.Model):
    """Stores AI-generated insights for each book"""
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='ai_insight')
    summary = models.TextField(blank=True, default='')
    sentiment = models.CharField(max_length=50, blank=True, default='')
    sentiment_score = models.FloatField(null=True, blank=True)
    predicted_genre = models.CharField(max_length=200, blank=True, default='')
    key_themes = models.TextField(blank=True, default='')  # JSON array as text
    generated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Insights for: {self.book.title}"


class BookChunk(models.Model):
    """Stores text chunks for RAG pipeline"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    content = models.TextField()
    chunk_id = models.CharField(max_length=200, unique=True)  # ID used in ChromaDB
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['book', 'chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.book.title}"


class ChatHistory(models.Model):
    """Stores user Q&A history"""
    question = models.TextField()
    answer = models.TextField()
    sources = models.TextField(blank=True, default='')  # JSON list of book titles cited
    asked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-asked_at']

    def __str__(self):
        return f"Q: {self.question[:80]}"
