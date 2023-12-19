from django.contrib import admin

from organization.models import Organization, OrganizationUnit, Terminal


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_key', 'iiko_server_login',
                    'iiko_server_password', 'iiko_url_server', 'iiko_port_server')


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'organization')


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'organization_unit',
                    'channel_name', 'plugin_online')

