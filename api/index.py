import os, sys

# Add the outer jobhub folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "jobhub"))

# Use your existing Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobhub.settings")

# Import the WSGI application
from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
