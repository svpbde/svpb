cd ..
# Delete and recreate database
sudo -u postgres dropdb --force --interactive svpbdata
sudo -u postgres createdb svpbdata
sudo -u postgres psql -c "grant all privileges on database svpbdata to svpbdb;"
# Init database with fixtures
python manage.py migrate
python manage.py loaddata mitglieder/fixtures/*.json
python manage.py loaddata arbeitsplan/fixtures/*.json
python manage.py loaddata boote/fixtures/*.json
