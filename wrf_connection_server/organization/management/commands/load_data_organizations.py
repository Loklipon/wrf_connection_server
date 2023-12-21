from django.core.management.base import BaseCommand

from organization.services import (get_organization_units_data_from_transport,
                                   get_terminals_data_from_transport, create_terminals_data)


class Command(BaseCommand):

    def handle(self, *args, **options):

        get_organization_units_data_from_transport()
        get_terminals_data_from_transport()
        create_terminals_data()


