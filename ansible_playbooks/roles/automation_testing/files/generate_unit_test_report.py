import datetime
import re
import os
import sys
from collections import OrderedDict


def search_test_case_names(results, status):
    results = re.findall(rf'(.*?)... {status}', results)
    names = list(OrderedDict.fromkeys(results))
    return names


def get_datetime():
    today = datetime.date.today()
    aux_date = today.strftime('%d-%B-%Y')
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return f'{aux_date} at {current_time}'


def generate_unit_test_report(raw_data, dest_path):
    """
    Generate a html report with the results of the unit testing
    """
    passed_tests = search_test_case_names(raw_data, 'ok')
    failed_tests = search_test_case_names(raw_data, 'FAIL')
    error_tests = search_test_case_names(raw_data, 'ERROR')

    # Generate html file
    file_html = open(f'{dest_path}', "w")

    html = '''<html>
    <head>
    <title>Unit testing results</title>
    <style>
        body {font-family: Helvetica, Arial, sans-serif;}
        .passed{color: green;}
        .failed{color: red;}
        table, th, td {
            border: 1px solid #e6e6e6;
            border-collapse: collapse;
            color: #999;
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            text-align: left;
            padding: 3px;}
    </style>
    </head> 
    <body>
    <h1>Unit Test Execution Results</h1>
    <p>Report generated on ''' + get_datetime() + '''</p>
    <h2>Results</h2>
    <table> 
      <thead>
        <tr>
          <th>Result</th>
          <th>Test</th>
        </tr>
      </thead>
      <tbody>'''
    for test in passed_tests:
        html += f"\n<tr><td><span class='passed'>Passed</span></td><td>{test}</td></tr>"
    for test in failed_tests:
        html += f"\n<tr><td><span class='failed'>Failed</span></td><td>{test}</td></tr>"
    for test in error_tests:
        html += f"\n<tr><td><span class='failed'>Error</span></td><td>{test}</td></tr>"
    html += "</tbody></table></body></html>"
    file_html.write(html)
    file_html.close()


def main():
    file_path = sys.argv[1]
    dest_path = sys.argv[2]
    if not os.path.exists(file_path):
        return "No Results"
    with open(file_path) as file:
        raw = file.read()
    generate_unit_test_report(raw, dest_path)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        pass
