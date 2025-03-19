import os
import time
import sys
import inventory_script
from requests.packages.urllib3 import disable_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from subprocess import check_output, CalledProcessError
from collections import Counter
disable_warnings(InsecureRequestWarning)
sys.path.append('../ansible_playbooks/')


def delete_merged_branches():
    delete_merged_branches_oneliner = """git fetch --all --prune && git branch --remote --merged origin/development | grep "^  origin/" |  cut -d/ -f2 | grep -v "^development$" | grep  -v "^staging$" | grep -v "^master$" | grep -v "^HEAD" |  xargs -t -I  '{branch}' git push origin --delete {branch}"""
    command = delete_merged_branches_oneliner
    return check_output(command.split()).decode().splitlines()


def git_branches(only_merged=False):
    """cause the gitlab api was acting up"""
    check_output('git fetch --prune'.split())
    command = 'git branch -r'
    if only_merged:
        command += ' --merged origin/development'
    remote_branches = check_output(command.split()).decode().splitlines()
    branch_names = [branch.split('origin/')[1] for branch in remote_branches
                    if branch.strip().startswith('origin/') and not branch.strip().startswith('origin/HEAD')]
    return branch_names


def get_branch_timestamp(branch, origin=True):
    if origin and not branch.startswith('origin/'):
        branch = f'origin/{branch}'
    command = f'git log --date=unix -1 --format=%cd {branch}'
    timestamp = int(check_output(command.split()).decode().strip())
    return timestamp


def branches_older_than(days=15):
    max_seconds = days * 24 * 60 * 60
    branch_names = git_branches()
    now = time.time()
    output = []
    for branch in branch_names:
        try:
            timestamp = get_branch_timestamp(branch)
            seconds_since = now - timestamp
            if seconds_since >= max_seconds:
                output.append(branch)
        except CalledProcessError:
            print(f'error with {branch}')
    return output


def is_waiting(results):
    statuses = [result.json().get('status') for result in results.values()]
    return 'INPROGRESS' in statuses or 'APPROVAL_PENDING' in statuses or 'PENDING' in statuses


def total_non_master(unity):
    count = 0
    for branch, servers in unity.get_managed_resources_by_branch().items():
        if branch not in ['master', 'development', 'staging']:
            count += len(servers)
    return count


def delete_old_servers():
    unity = inventory_script.Unity()
    resources = unity.get_managed_resources_by_branch()
    merged_branches = set(git_branches(only_merged=True)).intersection(set(resources))
    old_branches = set(branches_older_than()).intersection(set(resources))
    deleted_branches = set(resources).difference(set(git_branches()))
    protected_branches = set(('available', 'master', 'development', 'staging'))
    branches_to_delete = merged_branches.union(old_branches).union(deleted_branches).difference(protected_branches)
    print('Branches to delete:', ', '.join(branches_to_delete))
    results = {}
    for branch in branches_to_delete:
        for deployment in resources[branch]:
            deployment_id = deployment['unity_deployment_id']
            result = unity.expire_deployment(deployment_id)
            results[f'{branch}_{deployment_id}'] = result
    while is_waiting(results):
        time.sleep(20)
        for deployment, result in results.items():
            try:
                request_id = result.json()['id']
            except KeyError:
                continue
            uri = f'/deployment/api/requests/{request_id}'
            results[deployment] = unity.session.get(uri)
        statuses = Counter([result.json().get('status', 'error') for result in results.values()])
        for status, count in sorted(statuses.items(), key=lambda x: x[1]):
            print(status, count)
        print('\n', '-' * 10)


def generate_servers(max_servers):
    """
    Creates servers to reach the maximum amount specified
    :param max_servers: int
    :return:
    """
    unity = inventory_script.Unity()
    total_servers = total_non_master(unity)
    print('Current Total Servers', total_servers)
    print('Servers Requested:', max_servers - total_servers)
    while total_servers < max_servers:
        responses = []
        # Will create servers 5 at a time, unless the difference to max servers is less
        # than 5 until it reaches max_servers
        count = min(max_servers - total_servers, 5)
        for _ in range(count):
            time.sleep(5)
            request = unity.create_server(location='adc', wait=False)
            responses.append(request)
        for create_response in responses:
            deployment_id = create_response.json()[0]['deploymentId']
            print(unity.wait_for_build(deployment_id))
        total_servers = total_non_master(unity)
    return locals()


def main():
    if '--cleanup' in str(sys.argv):
        delete_old_servers()
    elif '--generate' in str(sys.argv):
        generate_servers(25)
    elif '--everything' in str(sys.argv):
        delete_old_servers()
        generate_servers(25)
    elif '--show' in str(sys.argv):
        unity = inventory_script.Unity()
        resources = unity.get_managed_resources_by_branch()
        merged_branches = set(git_branches(only_merged=True)).intersection(set(resources))
        old_branches = set(branches_older_than()).intersection(set(resources))
        deleted_branches = set(resources).difference(set(git_branches()))
        protected_branches = set(('available', 'master', 'development', 'staging'))
        branches_to_delete = merged_branches.union(old_branches).union(deleted_branches).difference(protected_branches)
        print('Branches to delete:')
        for x in branches_to_delete:
            print(x)
    elif '--delete_branches' in str(sys.argv):
        merged_branches = git_branches(only_merged=True)
        print('Branches to delete:')
        for x in merged_branches:
            print(x)


if __name__ == '__main__':
    main()
