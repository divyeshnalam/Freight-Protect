# serve_django.py
import os
from waitress import serve
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freightprotect.settings")
application = get_wsgi_application()

serve(application, host="0.0.0.0", port=1014)
    