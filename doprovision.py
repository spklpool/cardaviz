import digitalocean
import os
import time
from subprocess import Popen, PIPE, STDOUT

cardaviz_role_id = os.environ.get('cardaviz_role_id')
cardaviz_secret_id = os.environ.get('cardaviz_secret_id')
token = os.environ.get('DIGITALOCEAN_ACCESS_TOKEN')

droplet = digitalocean.Droplet(token=token,
                                name='Cardaviz2',
                                user_data="""#!/bin/bash
apt update -y 
ant upgrade -y
apt install -y certbot
apt install -y nginx
apt install -y python3-pip
apt install -y python3.10-venv
apt install -y apt-transport-https software-properties-common wget
apt install gpg
wget -O- https://apt.grafana.com/gpg.key | gpg --dearmor | tee /usr/share/keyrings/grafana.gpg >/dev/null
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee -a /etc/apt/sources.list.d/grafana.list
gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
apt update -y
apt install -y vault=1.12.2-1
apt install -y grafana
systemctl start grafana-server
systemctl enable grafana-server
cd /
git clone https://github.com/spklpool/cardaviz.git
cd /cardaviz
python3 -m venv /cardaviz/venv
/cardaviz/venv/bin/pip3 install -r requirements.txt
echo """ + cardaviz_role_id + """ > /cardaviz/cardaviz_role_id
echo """ + cardaviz_secret_id + """ > /cardaviz/cardaviz_secret_id
cp /cardaviz/etc/cardaviz_vault.service /etc/systemd/system/cardaviz_vault.service
systemctl start cardaviz_vault.service
systemctl enable cardaviz_vault.service
mkdir /var/www/html/mainnet_data
cp -r /cardaviz/data/* /var/www/html/mainnet_data/
chown -R root:www-data /var/www/html/mainnet_data/
cp /cardaviz/etc/cardaviz_backend.service /etc/systemd/system/cardaviz_backend.service
cp /cardaviz/etc/journald.conf /etc/systemd/journald.conf
systemctl restart systemd-journald
systemctl start cardaviz_backend.service
systemctl enable cardaviz_backend.service
cp /cardaviz/etc/nginx.conf /etc/nginx/nginx.conf
cp /cardaviz/etc/cardaviz.app /etc/nginx/sites-available/cardaviz.app
ln -s /etc/nginx/sites-available/cardaviz.app /etc/nginx/sites-enabled/cardaviz.app
cp /cardaviz/etc/options-ssl-nginx.conf /etc/letsencrypt/options-ssl-nginx.conf
cp /cardaviz/etc/ssl-dhparams.pem /etc/letsencrypt/ssl-dhparams.pem
systemctl restart nginx
""",
                                region='nyc3',
                                ssh_keys=['f9:c9:f9:d0:15:8a:5d:68:02:f5:9d:26:66:ff:a9:7f'],
                                image='ubuntu-22-04-x64',
                                size_slug='s-1vcpu-1gb-intel',
                                backups=False)


droplet.create()
status=''
while(not status == 'completed'):
    actions = droplet.get_actions()
    for action in actions:
        action.load()
        status = action.status
        print(status)
print('id: ' + str(droplet.id))

ip = None
while(ip == None):
    id = droplet.id
    created_droplet = digitalocean.Droplet.get_object(os.environ.get('DIGITALOCEAN_ACCESS_TOKEN'), id)
    created_droplet.load()
    ip = created_droplet.ip_address
    print('ip: ' + str(ip))

print('waiting 30 seconds to let the droplet time to install our public key')
time.sleep(30)

p = Popen(["ssh", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-i", "Sparkle.pem", "root@" + ip, "tail", "-f", "/var/log/cloud-init-output.log"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
for line in p.stdout:
    print(line)
    if b'Cloud-init' in line and b'finished at' in line:
        break
p.kill()

print('done provisionning droplet id ' + str(droplet.id) + ' at ip ' + str(ip))
print('rebooting to complete setup')

p = Popen(["ssh", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-i", "Sparkle.pem", "root@" + ip, "reboot", "now"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
time.sleep(10)
p.kill()

back_up = False
while(back_up == False):
    p = Popen(["ssh", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-i", "Sparkle.pem", "root@" + ip, "grep", "SPKL", "/var/www/html/mainnet_data/*.json"], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    for line in p.stdout:
        print(line)
        if b'Connection refused' in line:
            back_up = False
            time.sleep(5)
            break
        if b'SPKL' in line:
            back_up = True
            break

print('done rebooting droplet id ' + str(droplet.id) + ' at ip ' + str(ip))

