from locust import HttpUser, task

class HelloWorldUser(HttpUser):
    @task
    def hello_world(self):
        self.client.get("/pools/1pct")
        self.client.get("/ranking/underappreciated_performers")
        self.client.get("/pools/ATFF")
        self.client.get("/pools/SPKL")
        self.client.get("/")

    @task
    def ranking_user(self):
        self.client.get("/")
        self.client.get("/ranking/underappreciated_performers")

    @task
    def hello_world(self):
        self.client.get("/notarealthing")
        self.client.get("/mers")
        self.client.get("/pools/ATFF")
        self.client.get("/pools/SPKL")
        self.client.get("/pools/notapool")