#!/bin/bash
eval `ssh-agent -s`
ssh-add ~/.ssh/stixex.pem
alembic upgrade head