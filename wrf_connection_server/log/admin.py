from django.contrib import admin

from log.models import HttpLog, WsLog


@admin.register(HttpLog)
class HttpLogAdmin(admin.ModelAdmin):
    list_display = ('url', 'time', 'response_status')


@admin.register(WsLog)
class WsLogAdmin(admin.ModelAdmin):
    list_display = ('correlation_id', 'telegram_chat_id', 'time', 'method',
                    'terminal', 'status')
