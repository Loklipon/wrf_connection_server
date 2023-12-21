from django.urls import re_path as url
from iiko.consumers import IikoFrontConsumer

websocket_urlpatterns = [
    url('ws/front/', IikoFrontConsumer.as_asgi())
]
