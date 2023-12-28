import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wrf_connection_server.settings')
django.setup()


from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import wrf_connection_server.routing


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            wrf_connection_server.routing.websocket_urlpatterns
        )
    ),
})
