import uuid
from django.db import models

from organization.models import OrganizationUnit


class Client(models.Model):

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f'{self.name}'

    uuid = models.UUIDField(verbose_name='UUID сотрудника')
    name = models.CharField(max_length=200, verbose_name='Имя сотрудника')
    organization_unit = models.ForeignKey(OrganizationUnit, on_delete=models.CASCADE, related_name='client',
                                          verbose_name='Торговая точка')
    send_message = models.BooleanField(default=False, verbose_name='Может отправлять сообщения')
    get_message = models.BooleanField(default=False, verbose_name='Может получать сообщения')


class ClientPhone(models.Model):

    class Meta:
        verbose_name = 'Номер телефона клиента'
        verbose_name_plural = 'Номера телефонов клиентов'

    def __str__(self):
        return f'{self.client}'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='phone', verbose_name='Сотрудник')
    phone_number = models.CharField(max_length=200, verbose_name='Номер телефона сотрудника')
    telegram_chat_id = models.CharField(max_length=200, null=True, blank=True,
                                        verbose_name='Telegram chat ID')
    terminal_to_send = models.CharField(max_length=200, null=True, blank=True,
                                        verbose_name='UUID терминала для отправки сообщения')
