import sys
import os
import json
sys.path.append(sys.path[0].replace('ansible_playbooks', 'django_backend'))
sys.path.append(sys.path[0].replace('ansible_playbooks', 'python_packages/ndosecrets'))

from local_library.internal_services.tanium import Tanium


def main():
    username = os.environ.get('ANSIBLE_INVENTORY_USR')
    password = os.environ.get('ANSIBLE_INVENTORY_PSW')
    vault_auth = {"type": "ldap", "username": username, "password": password}
    tanium = Tanium(vault_auth=vault_auth)
    with open('branch_server.json', 'r') as f:
        ip_address = json.loads(f.read())[0]['ip_address']
        tanium.refresh_api_token(ip_addresses=[ip_address])
    print('We have created a new token!')


if __name__ == '__main__':
    main()
