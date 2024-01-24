from django.contrib import admin

from clients.models import Client, ClientPhone


class PhoneInLine(admin.TabularInline):
    model = ClientPhone
    extra = 0
    readonly_fields = ('telegram_chat_id', 'org_unit_to_send')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_organization_units', 'send_message')
    inlines = (PhoneInLine,)
    filter_horizontal = ('organization_unit',)
    readonly_fields = ('uuid',)

    def get_organization_units(self, obj):
        return ', '.join([org_unit.name for org_unit in obj.organization_unit.all()])

    get_organization_units.short_description = 'Торговые точки'

    def save_model(self, request, obj, form, change):
        ClientPhone.objects.filter(client=obj).update(org_unit_to_send=None)
        super().save_model(request, obj, form, change)
