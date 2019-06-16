# instructions for installation:
# 
# python3 create_remotecontrol_service.py
# sudo mv jetbot_remotecontrol.service /etc/systemd/system/jetbot_remotecontrol.service
# sudo systemctl enable jetbot_remotecontrol
# sudo systemctl start jetbot_remotecontrol
#
# above instructions are derived from https://github.com/NVIDIA-AI-IOT/jetbot/wiki/Create-SD-Card-Image-From-Scratch

import argparse
import getpass
import os

STATS_SERVICE_TEMPLATE = """
[Unit]
Description=JetBot Remote Control Service

[Service]
Type=simple
ExecStart=/usr/bin/python3 %s/jetbot/jetbot/apps/remotecontrol.py
WorkingDirectory=%s
Restart=always

[Install]
WantedBy=multi-user.target
"""

STATS_SERVICE_NAME = 'jetbot_remotecontrol'


def get_pwrbtn_service():
    return STATS_SERVICE_TEMPLATE % (os.environ['HOME'], os.environ['HOME'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='jetbot_remotecontrol.service')
    args = parser.parse_args()

    with open(args.output, 'w') as f:
        f.write(get_pwrbtn_service())
