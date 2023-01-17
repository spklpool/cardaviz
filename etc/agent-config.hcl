vault {
  address = "http://192.168.0.149:60005"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/home/ubuntu/cardaviz_role_id"
      secret_id_file_path = "/home/ubuntu/cardaviz_secret_id"
      remove_secret_id_file_after_reading = false
    }
  }
  sink "file" {
    config = {
      path = "/home/ubuntu/vault_token"
      mode = 0644
    }
  }
}
template {
  source = "/cardaviz/etc/database.ini.tmpl"
  destination = "/cardaviz/database.ini"
}
template {
  source = "/cardaviz/etc/cert.pem.tmpl"
  destination = "/etc/letsencrypt/live/cardaviz.app/cert.pem"
}
template {
  source = "/cardaviz/etc/chain.pem.tmpl"
  destination = "/etc/letsencrypt/live/cardaviz.app/chain.pem"
}
template {
  source = "/cardaviz/etc/fullchain.pem.tmpl"
  destination = "/etc/letsencrypt/live/cardaviz.app/fullchain.pem"
}
template {
  source = "/cardaviz/etc/privkey.pem.tmpl"
  destination = "/etc/letsencrypt/live/cardaviz.app/privkey.pem"
}