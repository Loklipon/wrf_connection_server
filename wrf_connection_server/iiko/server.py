import hashlib
import requests

from log.models import HttpLog


def add_log(response, body):
    HttpLog.objects.create(url=response.url,
                           request=body,
                           response=response.text,
                           response_status=response.status_code)


class IikoServer:

    def __init__(self, organization):
        self.login = organization.iiko_server_login
        self.password = organization.iiko_server_password
        self.host = organization.iiko_url_server
        self.port = organization.iiko_port_server
        self.url = self.host + ':' + self.port
        self.params = {'key': self._auth()}

    def __del__(self):
        self._logout()

    def _auth(self):
        method_url = '/resto/api/auth'
        url = self.url + method_url
        params = {
            'login': self.login,
            'pass': hashlib.sha1(self.password.encode('utf-8')).hexdigest()
        }
        response = requests.get(url, params=params)
        add_log(response, None)
        return response.text

    def _logout(self):
        method_url = '/resto/api/logout'
        url = self.url + method_url
        response = requests.get(url, params=self.params)
        add_log(response, None)

    def load_organization_units(self):
        method_url = '/resto/api/corporation/departments'
        url = self.url + method_url
        headers = {'Content-Type': 'application/xml'}
        params = self.params.copy()
        print(params)
        response = requests.get(url, headers=headers, params=params)
        add_log(response, None)
        return response
