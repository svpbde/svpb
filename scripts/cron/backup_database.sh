#!/bin/sh
set -u

source /home/svpb/svpb/scripts/cron/healthchecks.env

# Check if variable is defined
: "${HC_UUID_BACKUP_DATABASE:?HC_UUID_BACKUP_DATABASE unset or empty}"

# Ping healthchecks.io with start signal
curl -fsS -m 10 --retry 5 https://hc-ping.com/$HC_UUID_BACKUP_DATABASE/start
# The actual job to run
cd /home/svpb/svpb
timestamp=`date +%Y-%m-%dT%H%M%S`
msg=$(/home/svpb/svpb-venv/bin/python3 manage.py dumpdata --exclude=auth.permission --exclude=contenttypes --exclude=sessions -o "backup/${timestamp}_database_dump.json" 2>&1)
echo "$msg"
# Send finish ping with logs
curl -fsS -m 10 --retry 5 --data-raw "$msg" https://hc-ping.com/$HC_UUID_BACKUP_DATABASE/$?
