#!/bin/sh
set -u

source /home/svpb/svpb/scripts/cron/healthchecks.env

# Check if variable is defined
: "${HC_UUID_UPCOMING_JOBS_5:?HC_UUID_UPCOMING_JOBS_5 unset or empty}"

# Ping healthchecks.io with start signal
curl -fsS -m 10 --retry 5 https://hc-ping.com/$HC_UUID_UPCOMING_JOBS_5/start
# The actual job to run
cd /home/svpb/svpb
msg=$(/home/svpb/svpb-venv/bin/python3 manage.py notify_about_upcoming_jobs 5 2>&1)
echo "$msg"
# Send finish ping with logs
curl -fsS -m 10 --retry 5 --data-raw "$msg" https://hc-ping.com/$HC_UUID_UPCOMING_JOBS_5/$?
