#!/bin/bash

#Execute veracode scan
java -jar pipeline-scan.jar \
  --veracode_api_id "485d3449c5805cdae48a590ab6656962" \
  --veracode_api_key "${1}" \
  --file "frontend.zip" \
  --fail_on_severity="Very Low" \
  --timeout 10 \
  --project_name "NetDevOps_Portal" \
  --project_url "https://github.sys.cigna.com/cigna/NetDevOps-Portal.git" \
  --project_ref "${2}" \
  --issue_details "true" \
  --summary_output "true"\
  --summary_output_file "veracode_frontend_results.txt"