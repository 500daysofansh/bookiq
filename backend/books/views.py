"""
BookIQ API Views
All REST endpoints for the book platform
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Book, AIInsight, ChatHistory
from .serializers import (
    BookListSerializer, BookDetailSerializer,
    BookCreateSerializer, ChatHistorySerializer
)
from .ai_service import (
    generate_all_insights, index_book_for_rag,
    rag_query, get_recommendations, load_all_books_to_vector_store
)
from .scraper import scrape_books

logger = logging.getLogger(__name__)


class BookListView(APIView):
    """
    GET /api/books/ - List all books with optional filters
    """
    def get(self, request):
        books = Book.objects.all()

        # Optional filters
        genre = request.query_params.get('genre')
        search = request.query_params.get('search')
        sort = request.query_params.get('sort', '-rating')

        if genre:
            books = books.filter(genre__icontains=genre)
        if search:
            books = books.filter(title__icontains=search) | books.filter(author__icontains=search)

        # Sorting
        valid_sorts = ['title', '-title', 'rating', '-rating', 'created_at', '-created_at']
        if sort in valid_sorts:
            books = books.order_by(sort)

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(books, request)
        serializer = BookListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class BookDetailView(APIView):
    """
    GET /api/books/<id>/ - Full book details including AI insights
    """
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookDetailSerializer(book)
        return Response(serializer.data)


class BookRecommendationsView(APIView):
    """
    GET /api/books/<id>/recommendations/ - Get related book recommendations
    """
    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        all_books = list(Book.objects.exclude(pk=pk))
        recommendations = get_recommendations(book, all_books, top_n=6)

        return Response({
            'book_id': pk,
            'book_title': book.title,
            'recommendations': recommendations
        })


class ScrapeAndIngestView(APIView):
    """
    POST /api/scrape/ - Trigger book scraping and AI processing
    Body: {"max_pages": 3, "use_selenium": false}
    """
    def post(self, request):
        max_pages = int(request.data.get('max_pages', 3))
        use_selenium = bool(request.data.get('use_selenium', False))
        generate_insights = bool(request.data.get('generate_insights', True))

        # Cap at 10 pages to prevent abuse
        max_pages = min(max_pages, 10)

        try:
            # Step 1: Scrape books
            logger.info(f"Starting scrape: {max_pages} pages, selenium={use_selenium}")
            scraped_books = scrape_books(max_pages=max_pages, use_selenium=use_selenium)

            if not scraped_books:
                return Response({'error': 'No books scraped'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Step 2: Save to DB and generate insights
            created_count = 0
            updated_count = 0
            errors = []

            for book_data in scraped_books:
                try:
                    book, created = Book.objects.update_or_create(
                        title=book_data['title'],
                        defaults={
                            'author': book_data.get('author', ''),
                            'rating': book_data.get('rating'),
                            'num_reviews': book_data.get('num_reviews', 0),
                            'description': book_data.get('description', ''),
                            'genre': book_data.get('genre', ''),
                            'price': book_data.get('price', ''),
                            'availability': book_data.get('availability', ''),
                            'book_url': book_data.get('book_url', ''),
                            'cover_image_url': book_data.get('cover_image_url', ''),
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # Generate AI insights if requested
                    if generate_insights and book.description:
                        try:
                            insights = generate_all_insights(book)
                            AIInsight.objects.update_or_create(
                                book=book,
                                defaults=insights
                            )
                            # Update genre from AI if not already set
                            if not book.genre and insights.get('predicted_genre'):
                                book.genre = insights['predicted_genre']
                                book.save()
                        except Exception as e:
                            logger.warning(f"AI insight failed for {book.title}: {e}")
                            errors.append(f"AI insight failed for '{book.title}': {str(e)}")

                    # Index for RAG
                    index_book_for_rag(book)

                except Exception as e:
                    logger.error(f"Error saving book {book_data.get('title', '?')}: {e}")
                    errors.append(f"Failed to save '{book_data.get('title', '?')}': {str(e)}")

            return Response({
                'success': True,
                'total_scraped': len(scraped_books),
                'created': created_count,
                'updated': updated_count,
                'errors': errors[:10],  # Show first 10 errors
                'message': f"Successfully processed {created_count + updated_count} books"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Scrape endpoint error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManualBookUploadView(APIView):
    """
    POST /api/books/upload/ - Manually add a single book
    """
    def post(self, request):
        serializer = BookCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book = serializer.save()

        # Generate AI insights
        insights_data = None
        if book.description:
            try:
                insights = generate_all_insights(book)
                insight_obj = AIInsight.objects.create(book=book, **insights)
                insights_data = {
                    'summary': insight_obj.summary,
                    'genre': insight_obj.predicted_genre,
                    'sentiment': insight_obj.sentiment,
                }
                # Update genre
                if not book.genre and insight_obj.predicted_genre:
                    book.genre = insight_obj.predicted_genre
                    book.save()
            except Exception as e:
                logger.warning(f"AI insights failed: {e}")

        # Index for RAG
        index_book_for_rag(book)

        return Response({
            'book': BookDetailSerializer(book).data,
            'ai_insights': insights_data,
            'message': 'Book uploaded and processed successfully'
        }, status=status.HTTP_201_CREATED)


class RAGQueryView(APIView):
    """
    POST /api/ask/ - Ask a question about books using RAG pipeline
    Body: {"question": "What books are about love?"}
    """
    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)

        if len(question) > 500:
            return Response({'error': 'Question too long (max 500 chars)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure vector store is loaded
            load_all_books_to_vector_store()

            # Run RAG pipeline
            result = rag_query(question)

            # Save to chat history
            sources_str = str([s['title'] for s in result.get('sources', [])])
            ChatHistory.objects.create(
                question=question,
                answer=result['answer'],
                sources=sources_str,
            )

            return Response({
                'question': question,
                'answer': result['answer'],
                'sources': result.get('sources', []),
                'chunks_used': result.get('chunks_used', 0),
            })

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatHistoryView(APIView):
    """
    GET /api/chat-history/ - Get past Q&A history
    """
    def get(self, request):
        history = ChatHistory.objects.all()[:50]
        serializer = ChatHistorySerializer(history, many=True)
        return Response(serializer.data)


class GenreListView(APIView):
    """
    GET /api/genres/ - List all available genres
    """
    def get(self, request):
        from django.db.models import Count
        genres = (
            Book.objects
            .exclude(genre='')
            .values('genre')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response(list(genres))


class StatsView(APIView):
    """
    GET /api/stats/ - Platform statistics
    """
    def get(self, request):
        from django.db.models import Avg, Count
        stats = Book.objects.aggregate(
            total_books=Count('id'),
            avg_rating=Avg('rating'),
        )
        genre_count = Book.objects.exclude(genre='').values('genre').distinct().count()
        stats['total_genres'] = genre_count
        stats['total_qa'] = ChatHistory.objects.count()
        return Response(stats)
