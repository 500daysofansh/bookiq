from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'books'

    def ready(self):
        """
        Pre-load book chunks into the in-memory vector store.
        Uses post_migrate signal to avoid DB access during app init.
        """
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        def _load_vector_store(sender, **kwargs):
            try:
                from .ai_service import load_all_books_to_vector_store
                load_all_books_to_vector_store()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Vector store pre-load skipped: {e}")
        # Load lazily — views call load_all_books_to_vector_store() themselves too
