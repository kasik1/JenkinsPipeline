#! /usr/bin/env python

import sys
import time
import datetime
import random
import re
from pprint import pprint
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

hosts = sys.argv[2]
WEBEX_URL = "https://webexapis.com/v1/messages"
project = sys.argv[4]
token = sys.argv[3]


def webex_message(message, message_id=None):
    header = {'Authorization': 'Bearer ' + token}
    new_message = f"<blockquote class=info><h1>{project}</h1><br>{message}</blockquote>"
    # roomId is for Vault webex
    data = {"html": new_message,
            "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vN2NkNjIwYjAtZjk5My0xMWVkLThkMWUtNWRhMzk3Nzg3MzNk"}
    if message_id:
        message_url = f"https://webexapis.com/v1/messages/{message_id}"
        current = requests.get(message_url, headers=header, verify=False)
        current.raise_for_status()
        current_message = current.json().get('html')
        new_message = re.sub(r'</blockquote>', f'<br>{message}</blockquote>', current_message)
        if "failed" in message.lower():
            new_message = re.sub(r'class=(.*?)>', 'class="danger">', new_message)
        elif "success" in message.lower():
            new_message = re.sub(r'class=(.*?)>', 'class="success">', new_message)
        elif "info" in message.lower():
            new_message = re.sub(r'class=(.*?)>', 'class="primary">', new_message)
        data['html'] = new_message
        requests.put(message_url, json=data, headers=header, verify=False)
    else:
        response = requests.post(WEBEX_URL, json=data, headers=header, verify=False)
        return response.json().get('id')


if __name__ == "__main__":
    message_id = webex_message("Checking Vault Status", )
    status = 'Success'
    for address in hosts.split(','):
        vault_address = f'https://{address}:8200'
        unseal_keys = sys.argv[1].split(',')
        webex_message(f"Server: {address}", message_id)
        try:
            r = requests.get(f"{vault_address}/v1/sys/seal-status", verify=False)
            r.raise_for_status()
            data = r.json()
            if data.get('sealed'):
                webex_message("Detected sealed vault. Unsealing...", message_id)
                for i in random.sample(range(0, 4), 3):
                    payload = {"key": unseal_keys[i]}
                    r = requests.post(f"{vault_address}/v1/sys/unseal", json=payload, verify=False).json()
                if r.get('sealed'):
                    webex_message("Failed: Vault is still sealed", message_id)
                    status = 'Failed'
                else:
                    webex_message("Success: Vault has been unsealed", message_id)
            else:
                webex_message("Info: Vault is already unsealed", message_id)
        except Exception as e:
            webex_message(f"Error getting vault seal status:{e}", message_id)
            status = 'Failed'
    webex_message(f"Job Results: {status}", message_id)