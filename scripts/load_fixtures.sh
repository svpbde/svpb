cd .. 
rm svpb.sq 
python manage.py migrate
python manage.py loaddata mitglieder/fixtures/*.json
python manage.py loaddata arbeitsplan/fixtures/*.json
python manage.py loaddata boote/fixtures/*.json