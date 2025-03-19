#! /usr/bin/env python

import json
import os
import requests
import random
import sys
import time
import logging
from cached_property import cached_property
from collections import defaultdict
from getpass import getpass
from subprocess import check_output, CalledProcessError
from urllib.parse import urljoin

def colorize_log(level, message):
    colors = {
        'DEBUG': '\033[94m', #Blue
        'INFO': '\033[92m', #Green
        'WARNING': '\033[93m', #Yellow,
        'ERROR': '\033[91m', #Red
        'CRITICAL': '\033[95m', #Green
    }
    reset_code = '\033[0m'
    color_code = colors.get(level, '033[0m') #Default to no color if level is unknown
    return f"{color_code}{level}: {message}{reset_code}"

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        original_format = self._style._fmt
        #Insert the colorized level name and message into the format
        self._style._fmt = colorize_log (record.levelname, original_format)
        result = super().format(record)
        self._style._fmt = original_format
        return result

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
colored_formatter = ColoredFormatter('%(asctime)s %(name)s - %(levelname)s - %(message)s')
for handler in logger.handlers:
    handler.setFormatter(colored_formatter)


class UnitySession(requests.Session):
    _base_url = 'https://unity.internal.cigna.com'

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.verify = False

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self._base_url, url)
        return super().request(method, url, *args, **kwargs)


class Unity:
    login_uri = '/csp/gateway/am/api/login?access_token'
    other_login_uri = '/iaas/api/login'
    item_catalog_uri = '/catalog/api/items'
    deployment_uri = '/deployment/api/deployments'
    project_ids = {
        'ndoportal_PROD': '7c4dfa1a-a47a-4971-8fa7-3b5267692ff8',
        'ndoportal_NONPROD': 'ede935ec-d320-4f91-860c-e50f85ed819d',
        'ssot_cloud_PROD': 'd7fc82f7-2653-4356-b3aa-9b9693e4e2c2',
        'ssot_cloud_NONPROD': '3e4afd3d-16f7-4b0a-a5d4-d8cb59ebf7c8',
        'ndojenkins_PROD ': '367e0a66-54d9-4cd6-9e17-9d7d74a92d01',
        'ndojenkins_NONPROD': 'a78b4556-e0a9-4417-bc2a-db0e5bf68afb'
    }

    def get_all_generator(self, url, limit=20, project="ndoportal", **kwargs):
        finished = False
        params = kwargs.get('params', {})
        project_filter=f"{self.project_ids[project + '_NONPROD']},{self.project_ids[project + '_PROD']}"

        page = 0
        while not finished:
            params['page'] = page
            params['size'] = limit
            params['projects'] = project_filter
            response = self.session.get(url, params=params, **kwargs)
            thing = response.json().copy()
            thing.pop('content')
            for item in response.json()['content']:
                yield item
            page += 1

            finished = response.json().get('last', True)

    def get_all(self, url, **kwargs):
        return list(self.get_all_generator(url, **kwargs))

    def __init__(self,
                 branch_environment_variable='NDOBRANCH',
                 project_environment_variable='NDOPROJECT',
                 username_environment_variable='ANSIBLE_INVENTORY_USR',

                 password_environment_variable='ANSIBLE_INVENTORY_PSW',
                 username=None,
                 password=None,
                 branch=None):
        self.username = username
        self.password = password
        self.username_environment_variable = username_environment_variable
        self.password_environment_variable = password_environment_variable
        self.branch_environment_variable = branch_environment_variable
        self.project_environment_variable = project_environment_variable

        self._branch = branch
        self._managed_resources = None

    @staticmethod
    def get_branch_from_git():
        """checks local git repo for current branch"""
        branches = check_output('git branch'.split()).decode()
        current_branch = [branch[2:] for branch in branches.splitlines() if branch.startswith('*')][0]
        return current_branch

    @property
    def branch(self):
        """retrieve the current branch"""
        if not self._branch:
            self._branch = os.environ.get(self.branch_environment_variable)
        if not self._branch:
            try:
                self._branch = self.get_branch_from_git()
            except CalledProcessError:
                pass
        if not self._branch:
            self._branch = input('Which branch')
        return self._branch

    def create_server(self,
                      branch='available',
                      unity_project_name='ndoportal_NONPROD',
                      project='netdevops-portal',
                      memory=4,
                      cpu=2,
                      storage=50,
                      location='adc',
                      os_name='RHEL8',
                      environment='Development',
                      item_name='Red Hat Enterprise Linux',
                      domain="silver.com",
                      wait=True):
        inputs = dict()
        inputs['diskGrid'] = [{'vgname': 'appvg', 'size_gb': storage}]
        inputs['applications'] = []
        inputs['instanceCount'] = 1
        inputs['dataClassification'] = 'general'
        inputs['memoryGB'] = str(memory)
        inputs['cpu'] = str(cpu)
        inputs['location'] = location
        inputs['osVersion'] = os_name
        inputs['environment'] = environment
        inputs['domain'] = domain
        timestamp = str(time.time()).split('.')[0]
        deployment_name = f'{project} {branch} {timestamp}'.replace('.', '').strip()
        #print('deploymentname: ', deployment_name)
        project_id = self.projects[unity_project_name]
        item_id = self.items[item_name]

        payload = {'projectId': project_id,
                   'deploymentName': deployment_name,
                   'inputs': inputs}
        uri = f'/catalog/api/items/{item_id}/request'
        create_response = self.session.post(uri, json=payload)
        deployment_id = create_response.json()[0]['deploymentId']
        self.set_deployment_inventory_tag(deployment_id, branch=branch)
        if wait:
            self.wait_for_build(deployment_id)
        return create_response

    def get_deployment(self, deployment_id):
        uri = f'/deployment/api/deployments/{deployment_id}'
        return self.session.get(uri, params={'expand': 'resources'}).json()

    def wait_for_build(self, deployment_id):
        deployment = None
        try:
            deployment = self.get_deployment(deployment_id)
            status = deployment['status']
        except KeyError:
            return deployment
        while status == 'CREATE_INPROGRESS':
            time.sleep(30)
            try:
                deployment = self.get_deployment(deployment_id)
                status = deployment['status']
            except KeyError:
                return deployment

        return status

    @cached_property
    def session(self):
        session = UnitySession()
        self.login(session)
        return session

    def get_auth(self):
        if not self.username:
            self.username = os.environ.get(self.username_environment_variable)
        if not self.password:
            self.password = os.environ.get(self.password_environment_variable)
        if not self.username:
            self.username = input('username for unity: ')
        if not self.password:
            self.password = getpass('password for unity: ')

        return {'username': self.username, 'password': self.password}

    def login(self, session=None):
        if not session:
            session = self.session
        refresh_token_response = session.post(self.login_uri, json=self.get_auth())
        try:
            refresh_token = refresh_token_response.json()['refresh_token']
        except KeyError:
            return refresh_token_response
        token_response = session.post(self.other_login_uri, json={'refreshToken': refresh_token})
        token = token_response.json()['token']
        session.headers['Authorization'] = f"Bearer {token}"


    def deployments_generator(self):
        for deployment in self.get_all_generator(self.deployment_uri):
            yield deployment

    def get_deployments(self):
        return list(self.deployments_generator())

    def managed_resources_generator(self, branch=None):
        # need to add a global pagination
        for deployment in self.deployments_generator():
            tag = self.parse_inventory_tag(deployment)
            if tag and (not branch or branch and tag['branch'] == branch):
                full_deployment = self.get_deployment(deployment['id'])
                for managed_resource in self._inventory_from_deployment_generator(full_deployment):
                    yield managed_resource

    def get_managed_resources(self, branch=None):
        return list(self.managed_resources_generator(branch))

    def get_managed_resources_by_branch(self, branch=None):
        resources_by_branch = defaultdict(list)
        for resource in self.get_managed_resources(branch=branch):
            resources_by_branch[resource['branch']].append(resource)
        return resources_by_branch

    def get_current_branch_resources(self):
        return self.get_managed_resources_by_branch(branch=self.branch).get(self.branch, [])

    def get_items(self):
        return self.session.get(self.item_catalog_uri).json()['content']

    @cached_property
    def items(self):
        return {item['name']: item['id'] for item in self.get_items()}

    def get_projects(self):
        return self.session.get('/iaas/api/projects').json()['content']

    @cached_property
    def projects(self):
        return {project['name']: project['id'] for project in self.get_projects()}

    def get_machines(self):
        return self.session.get(self.machine_uri()).json()['content']

    @staticmethod
    def machine_uri(machine_id=''):
        return urljoin('/iaas/api/machines/', machine_id)

    def get_machine(self, machine_id):
        return self.session.get(self.machine_uri(machine_id)).json()

    def expire_deployment(self, deployment_id, archive=False, reason='No longer needed'):
        payload = {'actionId': 'Deployment.custom.expiredeployment',
                   'inputs': {'archive': archive},
                   'reason': reason}
        uri = f'/deployment/api/deployments/{deployment_id}/requests'
        return self.session.post(uri, json=payload)

    def delete_machine(self, machine_id):
        uri = self.machine_uri(machine_id)
        return self.session.delete(uri)

    def make_inventory(self):
        inventory = defaultdict(lambda: defaultdict(list))
        for server in self.get_current_branch_resources():
            for group in server['ansible_groups']:
                inventory[group]['hosts'].append(server['fqdn'])
        return inventory

    @staticmethod
    def create_inventory_tag(branch='available',
                             project='netdevops-portal',
                             ansible_groups=('DB', 'APP'),
                             ansible_variables=None):
        tag = dict()
        tag['ansible_variables'] = {}
        tag['branch'] = branch
        tag['project'] = project
        tag['ansible_groups'] = ansible_groups
        if ansible_variables:
            tag['ansible_variables'] = ansible_variables
        return json.dumps(tag)

    def set_deployment_inventory_tag(self, deployment_id,
                                     branch='available',
                                     project='netdevops-portal',
                                     ansible_groups=('DB', 'APP'),
                                     ansible_variables=None):

        json_tag = self.create_inventory_tag(branch, project, ansible_groups, ansible_variables)
        uri = f'/deployment/api/deployments/{deployment_id}'
        timestamp = str(time.time()).split('.')[0]
        name = f'{project} {branch} {timestamp}'.replace('.', '').strip()
        payload = {'name': name,
                   'description': json_tag}
        return self.session.patch(uri, json=payload)

    def claim_available_deployment(self, branch=None):
        if not branch:
            branch = self.branch
        available_resources = self.get_managed_resources_by_branch('available').get('available')
        if available_resources:
            resource = random.choice(available_resources)
            self.set_deployment_inventory_tag(resource['unity_deployment_id'], branch=branch)

    def get_host_variables(self, hostname):
        output = {}
        for server in self.get_current_branch_resources():
            if hostname in [server['name'], server['ip_address'], server['fqdn']]:
                output.update(server.get('ansible_variables', {}))
        return output

    @staticmethod
    def parse_inventory_tag(deployment):
        description = deployment.get('description', '')
        try:
            data = json.loads(description.strip())
        except json.JSONDecodeError:
            data = {}
        main_keys = ('project', 'branch')
        for key in main_keys:
            if key not in data:
                data = {}
        return data

    def _inventory_from_deployment_generator(self, deployment):
        tag = self.parse_inventory_tag(deployment)
        if tag:
            if deployment['inputs']['environment'] == 'Production':
                domain = 'internal.cigna.com'
            else:
                domain = 'silver.com'
            for resource in deployment['resources']:
                inventory_details = tag.copy()
                if resource['type'] == 'Cloud.vSphere.Machine':
                    try:
                        properties = resource['properties']
                        name = properties['resourceName']
                        inventory_details['name'] = name
                        inventory_details['ip_address'] = properties['address']
                        inventory_details['domain'] = domain
                        inventory_details['fqdn'] = f'{name}.{domain}'
                        inventory_details['unity_deployment_id'] = deployment['id']
                        yield inventory_details
                    except KeyError:
                        pass


def main():
    logging.debug('inventory_script.py: Starting process')
    unity_inventory = Unity()

    if '--list-all' in str(sys.argv):
        logging.info('inventory_script.py: Listing all servers in project [netdevops-portal]')
        inventory = unity_inventory.get_managed_resources_by_branch()
        print(json.dumps(inventory))
    
    elif '--list' in str(sys.argv):
        logging.info(f'inventory_script.py: Listing servers for branch [{unity_inventory.branch}] in project [netdevops-portal]')
        inventory = unity_inventory.make_inventory()
        print(json.dumps(inventory))

    elif '--host' in str(sys.argv):
        hostname = sys.argv[2]
        host_vars = unity_inventory.get_host_variables(hostname)
        print(json.dumps(host_vars))

    elif '--get-or-create' in str(sys.argv):
        inventory = unity_inventory.get_current_branch_resources()
        if not inventory:
            logging.info('inventory_script.py: No branch server found')
            logging.info('inventory_script.py: Attempting to claim [available] server')
            unity_inventory.claim_available_deployment()
        inventory = unity_inventory.get_current_branch_resources()

        if not inventory:
            logging.info('inventory_script.py: No [available] server found')
            logging.info('inventory_script.py: Attempting to create a server')
            create_response = unity_inventory.create_server(branch=unity_inventory.branch)
            deployment_id = create_response.json()[0]['deploymentId']
            unity_inventory.wait_for_build(deployment_id)

        inventory = unity_inventory.get_current_branch_resources()
        for server in inventory:
            unity_inventory.wait_for_build(server['unity_deployment_id'])
        inventory = unity_inventory.get_current_branch_resources()
        print(json.dumps(inventory))

    else:
        print()


if __name__ == '__main__':
    main()
