import os
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Jobhub.settings")

app = get_wsgi_application()

def handler(request, response):
    return app(request, response)

if __name__ == "__main__":
    execute_from_command_line(["manage.py", "runserver", "0.0.0.0:8000"])
