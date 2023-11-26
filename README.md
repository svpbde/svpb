svpb
====

Some simple Django webapps for the member area our sailing club "Segler-Verein Paderborn e.V." (SVPB).

Features
--------
* Manage tasks for obligatory working hours
  * Define tasks
  * Assign club members
  * Remind of upcoming tasks by e-mail
  * Report working hours
  * Accept reports
* Booking system for boats and boat crane
* Management of club members

Getting started
---------------
There are settings for three different environments:
1. **Local development** (`settings.local`):
   * If you want to develop in a local environment, you should know what you are doing.
   * Create your venv with Python 3.9.
   * Ensure xelatex is available to generate welcome letters for new members.
2. **Development VM (recommended)** (`settings.vm`):
   * There's a vagrant file to automatically provision a VM with ansible.
   Head over to [svpb-ansible](https://github.com/svpbde/svpb-ansible).
   * Execute `load_fixtures.sh` in `scripts` to populate the database with some test data.
   There are four users - "Vorstand", "Teamleiter", "Mitglied" and "Superuser", each with password "Test".
3. **Production**:
   * Install the production server according to the playbook in [svpb-ansible](https://github.com/svpbde/svpb-ansible).
   * Copy `settings/production.py.template` to `settings/production.py` and fill in the credentials.
   * In `manage.py` and `svpb/wsgi.py`, replace `settings.local`/`settings.vm` with `settings.production`.
   * Test email settings with `python manage.py sendtestemail <your-email-address>`.

Python dependencies are managed with [pip-tools](https://pip-tools.readthedocs.io/en/latest/).

Contributing
------------
Feel free to open issues or pull requests.
We are pleased about any kind of contribution!
Please adhere to [PEP8](https://peps.python.org/pep-0008/) and [commit.style](https://commit.style).
