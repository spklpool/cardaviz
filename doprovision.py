import digitalocean
import os

droplet = digitalocean.Droplet(token=os.environ.get('DIGITALOCEAN_ACCESS_TOKEN'),
                                name='Cardaviz1',
                                user_data="""#!/bin/bash
apt update -y 
ant upgrade -y
apt install -y nginx
apt install -y python3-pip
apt install -y python3.10-venv
cd /
git clone https://github.com/spklpool/cardaviz.git
cd /cardaviz
python3 -m venv /cardaviz/venv
/cardaviz/venv/bin/pip3 install -r requirements.txt
mkdir /var/www/html/data
cp -r /cardaviz/data/* /var/www/html/data/
chown -R root:www-data /var/www/html/data/
cp /cardaviz/etc/cardaviz_backend.service /etc/systemd/system/cardaviz_backend.service
systemctl start cardaviz_backend.service
systemctl enable cardaviz_backend.service
cp /cardaviz/etc/cardaviz_update.service /etc/systemd/system/cardaviz_update.service
systemctl start cardaviz_update.service
systemctl enable cardaviz_update.service
""",
                                region='nyc3',
                                ssh_keys=['f9:c9:f9:d0:15:8a:5d:68:02:f5:9d:26:66:ff:a9:7f'],
                                image='ubuntu-22-10-x64',
                                size_slug='s-1vcpu-1gb-intel',
                                backups=False)

#set Storage=persistent in
#/etc/systemd/journald.conf
# and
#systemctl restart systemd-journald

droplet.create()

print(droplet.ip_address)