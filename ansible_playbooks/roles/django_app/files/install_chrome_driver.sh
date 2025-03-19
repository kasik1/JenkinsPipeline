#!/bin/bash

chrome_version=`/opt/google/chrome/google-chrome --version | grep -oe "[0-9.]*" | rev | cut -d"." -f2,3,4 | rev`
chromedriver_version=`curl https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$chrome_version`
curl -O https://chromedriver.storage.googleapis.com/$chromedriver_version/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/bin/chromedriver
chmod 777 /usr/bin/chromedriver
