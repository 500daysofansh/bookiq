"""
DRF Serializers for Book API
"""
from rest_framework import serializers
from .models import Book, AIInsight, BookChunk, ChatHistory


class AIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = ['summary', 'sentiment', 'sentiment_score', 'predicted_genre', 'key_themes', 'generated_at']


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view"""
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'rating', 'num_reviews', 'genre',
                  'price', 'availability', 'book_url', 'cover_image_url', 'created_at']


class BookDetailSerializer(serializers.ModelSerializer):
    """Full serializer with AI insights"""
    ai_insight = AIInsightSerializer(read_only=True)

    class Meta:
        model = Book
        fields = '__all__'


class BookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author', 'rating', 'num_reviews', 'description',
                  'genre', 'price', 'availability', 'book_url', 'cover_image_url']


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = '__all__'
