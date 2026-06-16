"""
Run: python create_superuser.py
Creates admin user: admin / admin123
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookiq_backend.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@bookiq.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
