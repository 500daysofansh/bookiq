"""Django admin configuration for BookIQ models"""
from django.contrib import admin
from .models import Book, AIInsight, BookChunk, ChatHistory


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'genre', 'rating', 'num_reviews', 'availability', 'created_at']
    list_filter = ['genre', 'availability']
    search_fields = ['title', 'author', 'description']
    ordering = ['-rating']


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['book', 'predicted_genre', 'sentiment', 'sentiment_score', 'generated_at']
    list_filter = ['sentiment', 'predicted_genre']
    search_fields = ['book__title', 'summary']


@admin.register(BookChunk)
class BookChunkAdmin(admin.ModelAdmin):
    list_display = ['book', 'chunk_index', 'chunk_id']
    list_filter = ['book']


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['question', 'asked_at']
    ordering = ['-asked_at']
    readonly_fields = ['asked_at']
