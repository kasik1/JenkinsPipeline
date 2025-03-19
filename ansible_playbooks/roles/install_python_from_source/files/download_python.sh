#!/usr/bin/env bash
curl -O $1

if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi
if cat $2 | grep -q DOCTYPE; then
    echo download messed up, waiting 30 seconds and trying again
    rm $1
    sleep 30
    curl -O $1
else
    echo download successful
fi