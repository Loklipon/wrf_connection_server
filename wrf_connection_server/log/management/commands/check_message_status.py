import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bot.models import TelegramBot
from log.models import WsLog

from aiogram import Bot
from asgiref.sync import async_to_sync


def check_message_status():
    ws_logs = WsLog.objects.filter(status=None)
    uuid_list = ws_logs.values_list('correlation_id', flat=True).distinct()
    for uuid in uuid_list:

        if WsLog.objects.filter(correlation_id=uuid, status=True):
            qs = WsLog.objects.filter(correlation_id=uuid).exclude(status=True)
            last_log = qs.last()
            if last_log.time + timedelta(seconds=10) < timezone.now():
                qs.update(status=False)
                continue

        ws_logs_with_same_uuid = ws_logs.filter(correlation_id=uuid)
        last_ws_log = ws_logs_with_same_uuid.last()
        if last_ws_log.time + timedelta(seconds=10) < timezone.now():
            ws_logs_with_same_uuid.update(status=False)
            telegram_bot_data = TelegramBot.objects.first()
            telegram_bot = Bot(token=telegram_bot_data.token)
            async_to_sync(telegram_bot.send_message)(
                chat_id=last_ws_log.telegram_chat_id,
                text='Сообщение не было доставлено')


class Command(BaseCommand):

    def handle(self, *args, **options):

        for _ in range(5):
            check_message_status()
            time.sleep(10)

