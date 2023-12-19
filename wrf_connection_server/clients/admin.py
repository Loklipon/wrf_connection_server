from django.contrib import admin

from clients.models import Client, ClientPhone


class PhoneInLine(admin.TabularInline):
    model = ClientPhone
    extra = 0


@admin.register(Client)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_unit', 'send_message', 'get_message')
    inlines = (PhoneInLine,)
