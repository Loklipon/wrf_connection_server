from django.db import models


class Organization(models.Model):

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField(max_length=200, null=True, blank=True, verbose_name='Название организации')
    api_key = models.CharField(max_length=200, null=True, blank=True, verbose_name='API ключ')
    iiko_server_login = models.CharField(max_length=200, null=True, blank=True, verbose_name='Логин')
    iiko_server_password = models.CharField(max_length=200, null=True, blank=True, verbose_name='Пароль')
    iiko_url_server = models.CharField(max_length=200, null=True, blank=True, verbose_name='URL')
    iiko_port_server = models.CharField(max_length=200, null=True, blank=True, verbose_name='Порт')
    # tg_bot_token = models.CharField(max_length=200, null=True, blank=True, verbose_name='Токен Телеграм-бота')


class OrganizationUnit(models.Model):
    class Meta:
        verbose_name = 'Торговая точка'
        verbose_name_plural = 'Торговые точки'

    def __str__(self):
        return f'{self.name}'

    uuid = models.UUIDField(verbose_name='UUID торговой точки')
    name = models.CharField(max_length=200, verbose_name='Название торговой точки')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name='Организация')
    terminals_name_list = models.JSONField(null=True)
    terminals_dict = models.JSONField(null=True)


class Terminal(models.Model):

    class Meta:
        verbose_name = 'Терминал'
        verbose_name_plural = 'Терминалы'

    def __str__(self):
        return f'{self.name}'

    uuid = models.UUIDField(verbose_name='UUID терминала')
    name = models.CharField(max_length=200, verbose_name='Название терминала')
    organization_unit = models.ForeignKey(OrganizationUnit, on_delete=models.CASCADE, related_name='terminal',
                                          verbose_name='Торговая точка')
    channel_name = models.CharField(max_length=200, null=True)
    plugin_online = models.BooleanField(default=False, verbose_name='Плагин online')
