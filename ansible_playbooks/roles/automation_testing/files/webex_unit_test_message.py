#! /usr/bin/env python

from collections import OrderedDict
import datetime
import sys
import requests
import socket
import re
import os


def parse_test_results(results):
    """
    Takes a string of the stdout of unittest, returns a dict
    """
    try:
        results = dict(re.findall(r'(Ran|failures|errors|in)[\s=]([\d\.]+s?)', results))
        results['passed'] = int(results['Ran']) - (int(results['failures']) + int(results['errors']))
    except:
        return 'Failed to read unit test report'
    return results


def unit_testing_results(file_path):
    """
    Takes a path to a file of unit test stdout, returns a formatted string of the result summary
    """
    if not os.path.exists(file_path):
        return "No Results"
    with open(file_path) as file:
        raw = file.read()
    data = parse_test_results(raw)
    if 'Failed' in data:
        return data
    message = '=========== Unit testing: {passed} passed, {failures} failures, {errors} errors in {in} ==========='
    return message.format(**data)


def main():
    ut_file_location = sys.argv[3]  # Unit testing results
    message_id = sys.argv[2]
    token = sys.argv[1]
    header = {'Authorization': 'Bearer ' + token}
    url = f'https://webexapis.com/v1/messages/{message_id}'
    current = requests.get(url, headers=header, verify=False)
    current_message = current.json().get('html')
    hostname = socket.gethostname()
    unit_tests = unit_testing_results(ut_file_location)

    message = f"""<h3>Test Results: <a href=\"https://{hostname}/test_results/\" rel=\"nofollow\">View</a></h3><br>
              Unit testing<br>{unit_tests}<br><br>
              """
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
