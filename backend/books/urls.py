"""BookIQ URL Routes"""
from django.urls import path
from . import views

urlpatterns = [
    # Book endpoints
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/upload/', views.ManualBookUploadView.as_view(), name='book-upload'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/<int:pk>/recommendations/', views.BookRecommendationsView.as_view(), name='book-recommendations'),

    # AI / RAG
    path('ask/', views.RAGQueryView.as_view(), name='rag-query'),
    path('scrape/', views.ScrapeAndIngestView.as_view(), name='scrape'),

    # Utility
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('chat-history/', views.ChatHistoryView.as_view(), name='chat-history'),
]
