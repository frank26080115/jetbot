# instructions for installation:
# 
# python3 create_pwrbtn_service.py
# sudo mv jetbot_pwrbtn.service /etc/systemd/system/jetbot_pwrbtn.service
# sudo systemctl enable jetbot_pwrbtn
# sudo systemctl start jetbot_pwrbtn
#
# above instructions are derived from https://github.com/NVIDIA-AI-IOT/jetbot/wiki/Create-SD-Card-Image-From-Scratch

import argparse
import getpass
import os

STATS_SERVICE_TEMPLATE = """
[Unit]
Description=JetBot Power Button Service

[Service]
Type=simple
ExecStart=/usr/bin/python3 %s/jetbot/jetbot/apps/pwrbtn.py
WorkingDirectory=%s
Restart=always

[Install]
WantedBy=multi-user.target
"""

STATS_SERVICE_NAME = 'jetbot_pwrbtn'


def get_pwrbtn_service():
    return STATS_SERVICE_TEMPLATE % (os.environ['HOME'], os.environ['HOME'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='jetbot_pwrbtn.service')
    args = parser.parse_args()

    with open(args.output, 'w') as f:
        f.write(get_pwrbtn_service())
