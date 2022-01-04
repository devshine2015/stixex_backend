#!/bin/bash
eval `ssh-agent -s`
ssh-add ~/.ssh/stixex.pem
. venv/bin/activate
sudo supervisorctl stop all
sudo supervisorctl restart all
sleep 3
sudo supervisorctl status
