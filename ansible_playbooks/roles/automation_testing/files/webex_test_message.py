#! /usr/bin/env python
import sys
import requests
import re


def parse_pytest_results(file_location):
    """
    Parse the pytest-html results, returns a string
    """
    with open(file_location, 'r') as file:
        output = file.readlines()[-1]
    results = re.sub('\\x1b\[\d+m', '', output).strip()
    return results


def main():
    file_location = sys.argv[3]  # Smoke testing results
    if 'smoke' in file_location:
        test_type = 'Smoke'
    else:
        test_type = 'Functional'
        if 'api' in file_location:
            test_type += ' API'
        else:
            test_type += ' UI'

    message_id = sys.argv[2]
    token = sys.argv[1]
    header = {'Authorization': 'Bearer ' + token}
    url = f'https://webexapis.com/v1/messages/{message_id}'
    current = requests.get(url, headers=header, verify=False)
    current_message = current.json().get('html')
    testing_results = parse_pytest_results(file_location)

    message = f"{test_type} testing<br>{testing_results}<br><br>"
    new_message = re.sub('\<\/blockquote\>', f'<br>{message}</blockquote>', current_message)
    data = {"html": new_message,
            "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vNGVlNzE4ZTAtYWM3Mi0xMWVjLWIyYjgtYTEwMjU4NmU4MmFk"}
    requests.put(url, json=data, headers=header, verify=False)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        pass
