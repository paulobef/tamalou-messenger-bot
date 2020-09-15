# Copyright 2019 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Echo commands
set -v

# [START getting_started_gce_startup_script]
# Install Stackdriver logging agent
curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh
sudo bash install-logging-agent.sh

# Install or update needed software
apt-get update
apt-get install -yq git supervisor python python-pip
pip install --upgrade pip virtualenv

# Account to own server process
useradd -m -d /home/pythonapp pythonapp

# Fetch source code
export HOME=/root
git clone https://github.com/paulobef/tamalou-messenger-bot.git /opt/app/tamalou-messenger-bot

# remove any virtual env in the repo
rm -rf /opt/app/tamalou-messenger-bot/venv

# copy .env file in project
cp /opt/app/.env /opt/app/tamalou-messenger-bot

# move needed models into project (copy won't do it as it needs lotta spaaaaaace)
mv /opt/app/*.h5 opt/app/tamalou-messenger-bot/ml_models
mv /opt/app/cc.fr.300.bin opt/app/tamalou-messenger-bot

# Python environment setup
virtualenv -p python3 /opt/app/tamalou-messenger-bot/venv
source /opt/app/tamalou-messenger-bot/venv/bin/activate
/opt/app/tamalou-messenger-bot/venv/bin/pip install -r /opt/app/tamalou-messenger-bot/requirements.txt

# Set ownership to newly created account
chown -R pythonapp:pythonapp /opt/app

# Put supervisor configuration in proper place
cp /opt/app/tamalou-messenger-bot/tamalou-messenger-bot.conf /etc/supervisor/conf.d/tamalou-messenger-bot.conf

# Start service via supervisorctl
supervisorctl reread
supervisorctl update
# [END getting_started_gce_startup_script]