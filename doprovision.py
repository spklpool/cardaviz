import digitalocean
import os

cardaviz_role_id = os.environ.get('cardaviz_role_id')
cardaviz_secret_id = os.environ.get('cardaviz_secret_id')

droplet = digitalocean.Droplet(token=os.environ.get('DIGITALOCEAN_ACCESS_TOKEN'),
                                name='Cardaviz1',
                                user_data="""#!/bin/bash
apt update -y 
ant upgrade -y
apt install -y certbot
apt install -y nginx
apt install -y python3-pip
apt install -y python3.10-venv
sudo apt update && sudo apt install gpg
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update -y && sudo apt install -y vault=1.12.2-1
cd /
git clone https://github.com/spklpool/cardaviz.git
cd /cardaviz
python3 -m venv /cardaviz/venv
/cardaviz/venv/bin/pip3 install -r requirements.txt
echo """ + cardaviz_role_id + """ /cardaviz/cardaviz_role_id
echo """ + cardaviz_secret_id + """ /cardaviz/cardaviz_secret_id
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
""",
                                region='nyc3',
                                ssh_keys=['f9:c9:f9:d0:15:8a:5d:68:02:f5:9d:26:66:ff:a9:7f'],
                                image='ubuntu-22-04-x64',
                                size_slug='s-1vcpu-1gb-intel',
                                backups=False)

#set Storage=persistent in
#/etc/systemd/journald.conf
# and
#systemctl restart systemd-journald

droplet.create()

print(droplet.ip_address)
