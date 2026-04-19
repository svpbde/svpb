The scripts in this directory are intended to be run regularly via cron.
To check for successful execution, the service https://healthchecks.io is used.
The ping UUIDs have to be defined in the file healtchecks.env, so please copy healtchecks.env.template and fill in the UUIDs.
If you do not want to use healthchecks, just call the python commands directly in the crontab.
