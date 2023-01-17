server {
    server_name cardaviz.app www.cardaviz.app;
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/cardaviz.sock;
    }
    location /data {
        root  /var/www/html;
    }
    location /images {
        root  /var/www/html;
    }
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/cardaviz.app/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/cardaviz.app/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
server {
    if ($host = www.cardaviz.app) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    if ($host = cardaviz.app) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    server_name cardaviz.app www.cardaviz.app;
    listen 80;
    return 404; # managed by Certbot
}