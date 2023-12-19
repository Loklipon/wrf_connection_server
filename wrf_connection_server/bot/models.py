from django.db import models

from organization.models import OrganizationUnit


class TelegramBot(models.Model):

    class Meta:
        verbose_name = 'Телеграм-бот'
        verbose_name_plural = 'Телеграм-боты'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField(max_length=200, null=True, blank=True, verbose_name='Название бота')
    token = models.CharField(max_length=200, null=True, blank=True, verbose_name='Токен бота')