#!/bin/bash

rm -rf angular_frontend/node_modules
rm -f backend.zip frontend.zip pipeline-scan.jar
zip -r backend.zip django_backend
zip -r frontend.zip angular_frontend