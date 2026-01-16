from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """
        This runs once per user when they start.
        We first hit the homepage to obtain the CSRF cookie.
        """
        response = self.client.get("/")
        self.csrf_token = response.cookies.get("csrftoken")

    @task(2)
    def homepage(self):
        self.client.get("/")

    @task(1)
    def choose_ride(self):
        headers = {
            "X-CSRFToken": self.csrf_token
        }

        self.client.post(
            "/choose-ride/",
            data={
                "pickup": "Andheri",
                "drop": "Bandra"
            },
            headers=headers,
            name="POST /choose-ride"
        )