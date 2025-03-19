#!/bin/bash

# results for api testing
tests=`grep "^collected" api_testing_results.txt | awk -F "/" '{print $3}' | awk '{print $1}'`
failed=`tail -1 api_testing_results.txt | awk -F "," '{print $1}'|awk '{print $2}'`
passed=`tail -1 api_testing_results.txt| awk -F "," '{print $2}' | awk '{print $1}'`
skip=`tail -1 api_testing_results.txt| awk -F "," '{print $3}' | awk '{print $1}'`
warns=`tail -1 api_testing_results.txt| awk -F "," '{print $4}' | awk '{print $1}'`
t_time=`tail -1 api_testing_results.txt | awk '{print $(NF-2)}'`

# results for ui testing
ui_test=`grep "^collected" ui_testing_results.txt | awk -F "/" '{print $3}' | awk '{print $1}'`
ui_fail=`tail -1 ui_testing_results.txt | awk -F "," '{print $1}'|awk '{print $2}'`
ui_pass=`tail -1 ui_testing_results.txt| awk -F "," '{print $2}' | awk '{print $1}'`
ui_skip=`tail -1 ui_testing_results.txt| awk -F "," '{print $3}' | awk '{print $1}'`
ui_warn=`tail -1 ui_testing_results.txt| awk -F "," '{print $4}' | awk '{print $1}'`
uit_time=`tail -1 ui_testing_results.txt | awk '{print $(NF-2)}'`

t_stamp=`date +"%X %a %d %b %Y"`
server_name=`hostname -f`

curl -i -X POST --data-urlencode  'payload={
  "icon_url": "https://www.mattermost.org/wp-content/uploads/2016/04/icon.png",
  "text": "#### Automation Testing Results for Branch: '"${1}"' \n ##### View Results [(click to view)](https://'"${server_name}"'/admin/login/?next=/test_results/) \n
  | Component   | Tests Run   |  Passed   |  Failed   |  Warning  |   Skipped  | Time Taken |
  |:------------|:-----------:|:---------:|:---------:|:---------:|:----------:|:----------:|
  | api_testing | '"${tests}"'| '"${passed}"'| '"${failed}"'| '"${warns}"'|'"${skip}"'|'"${t_time}"' |
  | ui_testing  | '"${ui_tests}"'| '"${ui_pass}"'| '"${ui_fail}"'| '"${ui_warn}"'|'"${ui_skip}"'|'"${uit_time}"' |
  |             |             |           |           |           |            |            |
  "
  }' https://mm.sys.cigna.com/hooks/${2}
