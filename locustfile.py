from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Get CSRF + session
        response = self.client.get("/")
        self.csrf_token = response.cookies.get("csrftoken")

    @task
    def choose_ride(self):
        self.client.get(
            "/choose-ride/",
            params={
                "pickup": "Andheri",
                "dropoff": "Bandra",
                "distance_km": "7.5",
                "duration_min": "20",
                "ride_type": "daily"
            },
            name="GET /choose-ride"
        )