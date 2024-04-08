from locust import HttpUser, task

class HelloWorldUser(HttpUser):
    @task
    def hello_world(self):
        self.client.get("/pools/pool10q33p4hx4wqum6thmglw7z5l2vaay4w6m5cdq8fnurw7vjdppcf") #SPKL
        self.client.get("/ranking/underappreciated_overperformers")
        self.client.get("/pools/pool1lvsa8e0dw6z8g2fkw7prnfa7627wuy5jjexaadck6w5sxw5xkvm") #DIGI2
        self.client.get("/pools/pool1c2utlagkpht4zj0jetsf245c258geuxnjqp9kf4f2z9rutx9dz4") #QCPOL
        self.client.get("/")

    @task
    def ranking_user(self):
        self.client.get("/")
        self.client.get("/ranking/overappreciated_underperformers")

    @task
    def hello_world(self):
        self.client.get("/pools/pool1a4qtpgce7cu6wzc79fx7qrc3938hkl2gf8c2h5jugvm2gnu86l7") #HODLA
        self.client.get("/pools/pool1wp7vqk4mkx0w0wxzpy8avhft4qwcg60xldwem2uh9n4pw777fhz") #BEEHI
