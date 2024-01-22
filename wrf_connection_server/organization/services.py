import json
import xml.etree.ElementTree as ET

from iiko.server import IikoServer
from iiko.transport import IikoTransport
from organization.dataclasses.organizations import OrganizationUnitsList, TerminalGroupsList, TerminalGroup
from organization.models import Organization, OrganizationUnit, TerminalGroup


def get_organization_unit_data_from_server():
    if organization := Organization.objects.first():
        iiko_server = IikoServer(organization)
        response = iiko_server.load_organization_units()
        if response.status_code == 200:
            organization_units_xml_tree = ET.ElementTree(ET.fromstring(response.text))
            for organization_unit in organization_units_xml_tree.iter('corporateItemDto'):
                organization_type = organization_unit.find('type').text
                if organization_type == 'DEPARTMENT':
                    organization_unit_name = organization_unit.find('name').text
                    organization_unit_uuid = organization_unit.find('id').text
                    OrganizationUnit.objects.update_or_create(
                        uuid=organization_unit_uuid,
                        defaults={'name': organization_unit_name, 'org': organization})


def get_organization_units_data_from_transport():
    if organization := Organization.objects.first():
        iiko_transport = IikoTransport(organization)
        response = iiko_transport.load_organization_units()
        if response.status_code == 200:
            organization_units = OrganizationUnitsList.model_validate_json(response.text)
            for organization_unit in organization_units.organizations:
                OrganizationUnit.objects.update_or_create(
                    uuid=organization_unit.uuid,
                    defaults={'name': organization_unit.name, 'organization': organization}
                )


def get_terminals_data_from_transport():
    if organization := Organization.objects.first():
        if organization_units_uuids := list(OrganizationUnit.objects.values_list('uuid', flat=True).distinct()):
            organization_units_uuid_list = [str(uuid) for uuid in organization_units_uuids]
            iiko_transport = IikoTransport(organization)
            response = iiko_transport.load_terminal_group(organization_units_uuid_list)
            if response.status_code == 200:
                terminal_group_list = TerminalGroupsList.model_validate_json(response.text)
                for terminal_group in terminal_group_list.terminal_groups:
                    for terminal in terminal_group.terminals:
                        organization_unit = OrganizationUnit.objects.get(uuid=terminal.org_unit_uuid)
                        TerminalGroup.objects.update_or_create(
                            uuid=terminal.uuid,
                            defaults={'name': terminal.name, 'organization_unit': organization_unit}
                        )


def split_terminal_group_list(split_terminals_list, terminals_list):
    while len(terminals_list) > 1:
        var_list = list()
        var_list.append(terminals_list.pop(0))
        var_list.append(terminals_list.pop(0))
        split_terminals_list.append(var_list)
        split_terminals_list, terminals_list = split_terminal_group_list(split_terminals_list, terminals_list)
        break
    if len(terminals_list) == 1:
        split_terminals_list.append([terminals_list.pop(0)])
    return split_terminals_list, terminals_list


def create_terminals_data():
    if organization := Organization.objects.first():
        for organization_unit in OrganizationUnit.objects.filter(organization=organization):
            if terminals := TerminalGroup.objects.filter(
                    organization_unit=organization_unit).values_list('name', flat=True).distinct():
                terminals_list = list(terminals)
                split_terminal_list = list()
                split_terminal_list, _ = split_terminal_group_list(split_terminal_list, terminals_list)
                organization_unit.terminals_name_list = json.dumps(
                    split_terminal_list, ensure_ascii=False).encode('utf8').decode()
                all_terminals = TerminalGroup.objects.filter(organization_unit=organization_unit)
                terminals_dict = dict()
                for terminal in all_terminals:
                    terminals_dict[f'{terminal.name}'] = f'{terminal.uuid}'
                organization_unit.terminals_dict = json.dumps(
                    terminals_dict, ensure_ascii=False).encode('utf8').decode()
                organization_unit.save()


def create_organization_units_dict():
    if organization := Organization.objects.first():
        org_unit_dict = dict()
        for org_unit in OrganizationUnit.objects.filter(organization=organization):
            org_unit_dict[f'{org_unit.name}'] = f'{org_unit.uuid}'
        organization.organization_units_dict = org_unit_dict
        organization.save()


def load_organization_data():
    get_organization_units_data_from_transport()
    get_terminals_data_from_transport()
    create_organization_units_dict()
