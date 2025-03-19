#!/usr/bin/env bash

rm -rf angular_frontend/node_modules
rm -f backend.zip frontend.zip pipeline-scan.jar
zip -r backend.zip django_backend
zip -r frontend.zip angular_frontend

#Download veracode pipeline scan jar
curl -O  https://downloads.veracode.com/securityscan/pipeline-scan-LATEST.zip

#Unzip pipeline scan jar
unzip pipeline-scan-LATEST.zip pipeline-scan.jar


# Execute the backend scan
java -jar pipeline-scan.jar \
  --veracode_api_id "485d3449c5805cdae48a590ab6656962" \
  --veracode_api_key "${1}" \
  --file "backend.zip" \
  --fail_on_severity="Very Low" \
  --timeout 10 \
  --project_name "NetDevOps_Portal" \
  --project_url "https://github.sys.cigna.com/cigna/NetDevOps-Portal.git" \
  --project_ref "${2}" \
  --issue_details "true" \
  --summary_output "true"\
  --summary_output_file "veracode_backend_results.txt" \
  --json_output_file "veracode_backend_results.json"

#Execute frontend  scan
java -jar pipeline-scan.jar \
  --veracode_api_id "485d3449c5805cdae48a590ab6656962" \
  --veracode_api_key "${1}" \
  --file "frontend.zip" \
  --fail_on_severity="Very Low" \
  --timeout 10 \
  --project_name "NetDevOps_Portal" \
  --project_url "https://git.sys.cigna.com/NetworkServices-NetDevOps/netdevops-portal.git" \
  --project_ref "${2}" \
  --issue_details "true" \
  --summary_output "true"\
  --summary_output_file "veracode_frontend_results.txt"
  --json_output_file "veracode_frontend_results.json"

cp veracode_*_results.* veracode_*_results.* ~/test_results/