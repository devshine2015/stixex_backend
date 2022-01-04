#!/bin/bash
eval `ssh-agent -s`
ssh-add ~/.ssh/stixex.pem
. venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl stop all
sudo service postgresql restart
alembic upgrade head
sudo supervisorctl restart all
sleep 3
sudo supervisorctl status
