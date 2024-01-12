from django.contrib import admin

from clients.models import Client, ClientPhone


class PhoneInLine(admin.TabularInline):
    model = ClientPhone
    extra = 0


@admin.register(Client)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_organization_units', 'send_message')
    inlines = (PhoneInLine,)
    filter_horizontal = ('organization_unit',)

    def get_organization_units(self, obj):
        return ', '.join([org_unit.name for org_unit in obj.organization_unit.all()])

    get_organization_units.short_description = 'Торговые точки'
