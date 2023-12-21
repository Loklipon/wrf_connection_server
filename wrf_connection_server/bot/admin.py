from django.contrib import admin

from bot.models import TelegramBot


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'token')
