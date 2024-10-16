"""
WSGI config for eventsphere project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventsphere.settings")

application = get_wsgi_application()
