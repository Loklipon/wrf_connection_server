import json
import requests
from .server import add_log


class IikoTransport:

    def __init__(self, organization):
        self.url = 'https://api-ru.iiko.services/api/1'
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self._auth(organization.api_key)}'}

    def _auth(self, api_key):
        url = self.url + '/access_token'
        headers = {'Content-Type': 'application/json'}
        body = {'apiLogin': api_key}
        body = json.dumps(body)
        response = requests.post(url, data=body, headers=headers)
        add_log(response, body)
        return json.loads(response.text)['token']

    def load_organization_units(self):
        url = self.url + '/organizations'
        body = {'organizationIds': [],
                'returnAdditionalInfo': False,
                'includeDisabled': False}
        body = json.dumps(body)
        response = requests.post(url, headers=self.headers, data=body)
        add_log(response, body)
        return response

    def load_terminal_group(self, org_unit_uuid_list):
        url = self.url + '/terminal_groups'
        body = {'organizationIds': org_unit_uuid_list,
                'includeDisabled': True,
                'returnExternalData': []}
        body = json.dumps(body)
        response = requests.post(url, headers=self.headers, data=body)
        add_log(response, body)
        return response


