from django.db import models


class HttpLog(models.Model):

    class Meta:
        verbose_name = 'Лог'
        verbose_name_plural = 'HTTP'

    def __str__(self):
        return f'{self.url}'

    url = models.URLField(max_length=200, verbose_name='URL запроса')
    time = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    request = models.TextField(null=True, verbose_name='Body запроса', )
    response_status = models.CharField(max_length=200, null=True, verbose_name='Статус ответа')
    response = models.TextField(null=True, verbose_name='Body ответа')


class WsLog(models.Model):

    class Meta:
        verbose_name = 'Лог'
        verbose_name_plural = 'WS'

    def __str__(self):
        return f'Лог {self.pk}'

    correlation_id = models.UUIDField(verbose_name='UUID')
    telegram_chat_id = models.CharField(max_length=200, null=True, verbose_name='Telegram-chat ID')
    request = models.JSONField(null=True)
    response = models.JSONField(null=True)
    time = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    method = models.CharField(max_length=200, null=True, verbose_name='Метод')
    terminal = models.UUIDField(verbose_name='UUID терминала', null=True)
    status = models.BooleanField(verbose_name='Статус доставки сообщения', null=True)
