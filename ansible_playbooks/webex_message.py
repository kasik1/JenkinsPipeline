#! /usr/bin/env python

import sys
import requests
import re


def main():
    token = sys.argv[1]
    header = {'Authorization': 'Bearer ' + token}
    message = sys.argv[2]
    branch = sys.argv[3]
    url = f"https://webexapis.com/v1/messages"
    git_link = f"https://github.sys.cigna.com/cigna/NetDevOps-Portal/tree/{branch}"
    job_url = sys.argv[4]
    build_url = sys.argv[5]
    if branch == 'master':
        server_info = "netdevopsportal.sys.cigna.com"
    else:
        server_info = sys.argv[6]
    try:
        message_id = sys.argv[7]
    except IndexError:
        message_id = None
    if message_id:
        url = f"https://webexapis.com/v1/messages/{message_id}"
        current = requests.get(url, headers=header, verify=False)
        current_message = current.json().get('html')
        if server_info != 'Unknown':
            current_message = re.sub('Unknown', server_info, current_message)
        new_message = re.sub('\<\/blockquote\>', f'<br>{message}</blockquote>', current_message)
        if message.lower() == "failure":
            new_message = re.sub('class=(.*?)\>', 'class="danger">', new_message)
        elif message.lower() == 'success':
            new_message = re.sub('class=(.*?)\>', 'class="success">', new_message)
        elif message.lower() == 'job aborted':
            new_message = re.sub('class=(.*?)\>', 'class="primary">', new_message)
        data = {"html": new_message,
                "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vNGVlNzE4ZTAtYWM3Mi0xMWVjLWIyYjgtYTEwMjU4NmU4MmFk"}
        requests.put(url, json=data, headers=header, verify=False)
        print(message_id)
    else:
        sonar_link = ''
        zephyr_link = ''
        if branch.startswith('PR-'):
            pr_number = branch.split('PR-')[1]
            sonar_url = f"https://sonarqube.sys.cigna.com/dashboard?pullRequest={pr_number}&id=NetDevOps-Portal"
            sonar_link = f' | <a href=\"{sonar_url}\" rel=\"nofollow\">SonarQube</a>'
            zephyr_url = 'https://cigna.yourzephyr.com/flex/html5/release/6011'
            zephyr_link = f' | <a href=\"{zephyr_url}\" rel=\"nofollow\">Zephyr</a>'
        message = f"<blockquote class=info><h1>{branch}</h1><br>" \
                  f"<a href=\"{git_link}\" rel=\"nofollow\">Git</a> | " \
                  f"<a href=\"{job_url}/\" rel=\"nofollow\">Jenkins Job</a> | " \
                  f"<a href=\"{build_url}\" rel=\"nofollow\">Console</a>" \
                  f"{sonar_link}" \
                  f"{zephyr_link}<br>" \
                  f"<a href=\"https://{server_info}\" rel=\"nofollow\">https://{server_info}</a> | <a rel=\"nofollow\">ssh://{server_info}</a><br>{message}</blockquote>"
        data = {"html": message,
                "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vNGVlNzE4ZTAtYWM3Mi0xMWVjLWIyYjgtYTEwMjU4NmU4MmFk"}
        response = requests.post(url, json=data, headers=header, verify=False)
        print(response.json().get('id'))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        pass
