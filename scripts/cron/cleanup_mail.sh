#!/bin/sh
set -u

source /home/svpb/svpb/scripts/cron/healthchecks.env

# Check if variable is defined
: "${HC_UUID_CLEANUP_MAIL:?HC_UUID_CLEANUP_MAIL unset or empty}"

# Ping healthchecks.io with start signal
curl -fsS -m 10 --retry 5 https://hc-ping.com/$HC_UUID_CLEANUP_MAIL/start
# The actual job to run
cd /home/svpb/svpb
msg=$(/home/svpb/svpb-venv/bin/python3 manage.py cleanup_mail --days 90 --delete-attachments 2>&1)
echo "$msg"
# Send finish ping with logs
curl -fsS -m 10 --retry 5 --data-raw "$msg" https://hc-ping.com/$HC_UUID_CLEANUP_MAIL/$?
