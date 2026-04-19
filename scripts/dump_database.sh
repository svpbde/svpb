#!/bin/sh
timestamp=`date +%Y-%m-%dT%H%M%S`
cd ..
python manage.py dumpdata --exclude=auth.permission --exclude=contenttypes --exclude=sessions -o "backup/${timestamp}_database_dump.json"
