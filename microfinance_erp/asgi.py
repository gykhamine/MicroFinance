import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.notifications.routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'microfinance_erp.settings')
application = ProtocolTypeRouter({"http": get_asgi_application(),"websocket": AuthMiddlewareStack(URLRouter(apps.notifications.routing.websocket_urlpatterns))})
