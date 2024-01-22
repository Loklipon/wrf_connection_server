from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from organization.models import Organization, OrganizationUnit, TerminalGroup, Terminal
from organization.services import load_organization_data

from requests.exceptions import ConnectTimeout


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_key', 'iiko_server_login',
                    'iiko_server_password', 'iiko_url_server', 'iiko_port_server')
    readonly_fields = ('organization_units_dict',)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if Organization.objects.filter(pk=object_id):
            self.change_form_template = 'admin/change_view_organization.html'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def response_change(self, request, obj):
        if '_load-org-data' in request.POST:
            try:
                load_organization_data()
            except ConnectTimeout:
                messages.error(request, 'Ошибка загрузки данных. Сервис временно не доступен')
                return HttpResponseRedirect('../')
            except Exception as e:
                messages.error(request, f'Ошибка загрузки данных. Текст ошибки: {str(e)}')
                return HttpResponseRedirect('../')
            messages.success(request, 'Данные успешно загружены')
            return HttpResponseRedirect('../')
        return super().response_change(request, obj)


class TerminalGroupInLine(admin.TabularInline):
    model = TerminalGroup
    extra = 0
    readonly_fields = ('get_name', 'uuid', 'terminals_online')
    fields = ('get_name', 'uuid', 'terminals_online')

    def terminals_online(self, obj):
        all_terminals = obj.terminal.all().count()
        online_terminals = obj.terminal.filter(plugin_online=True).count()
        return f'{online_terminals}/{all_terminals}'

    terminals_online.short_description = 'Терминалов онлайн'

    def get_name(self, obj):
        return format_html(
            "<a href='{}'>{}</a>".format(reverse(f'admin:organization_terminalgroup_change',
                                                 args=(obj.pk,)), obj.name))

    get_name.short_description = 'Терминальная группа'


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'organization')
    inlines = (TerminalGroupInLine,)


class TerminalInLine(admin.TabularInline):
    model = Terminal
    extra = 0
    readonly_fields = ('name', 'uuid', 'channel_name', 'plugin_online')


@admin.register(TerminalGroup)
class TerminalGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'organization_unit')
    inlines = (TerminalInLine,)
