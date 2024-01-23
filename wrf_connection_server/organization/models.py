from django.db import models


class Organization(models.Model):

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField(max_length=200, null=True, verbose_name='Название организации')
    api_key = models.CharField(max_length=200, null=True, verbose_name='API ключ')
    iiko_server_login = models.CharField(max_length=200, null=True, blank=True, verbose_name='Логин')
    iiko_server_password = models.CharField(max_length=200, null=True, blank=True, verbose_name='Пароль')
    iiko_url_server = models.CharField(max_length=200, null=True, blank=True, verbose_name='URL')
    iiko_port_server = models.CharField(max_length=200, null=True, blank=True, verbose_name='Порт')
    organization_units_dict = models.JSONField(null=True, blank=True)


class OrganizationUnit(models.Model):
    class Meta:
        verbose_name = 'Торговая точка'
        verbose_name_plural = 'Торговые точки'

    def __str__(self):
        return f'{self.name}'

    uuid = models.UUIDField(verbose_name='UUID торговой точки')
    name = models.CharField(max_length=200, verbose_name='Название торговой точки')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name='Организация')


class TerminalGroup(models.Model):

    class Meta:
        verbose_name = 'Терминальная группа'
        verbose_name_plural = 'Терминальные группы'

    def __str__(self):
        return f'{self.name}'

    uuid = models.UUIDField(verbose_name='UUID терминальной группы')
    name = models.CharField(max_length=200, verbose_name='Название терминальной группы')
    organization_unit = models.ForeignKey(OrganizationUnit, on_delete=models.CASCADE, related_name='terminalgroup',
                                          verbose_name='Торговая точка')


class Terminal(models.Model):

    class Meta:
        verbose_name = 'Терминал'
        verbose_name_plural = 'Терминалы'

    def __str__(self):
        return f'{self.name}'

    uuid = models.UUIDField(verbose_name='UUID терминала')
    name = models.CharField(max_length=200, verbose_name='Название терминала')
    channel_name = models.CharField(max_length=200, null=True, blank=True)
    plugin_online = models.BooleanField(default=False, verbose_name='Плагин online')
    terminal_group = models.ForeignKey(TerminalGroup, on_delete=models.CASCADE, related_name='terminal',
                                       verbose_name='Терминальная группа')
