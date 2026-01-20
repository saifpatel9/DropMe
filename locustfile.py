from locust import HttpUser, task, between

class TestUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """
        Simulate landing on homepage like a browser.
        Session creation only.
        """
        self.client.get("/")

    @task
    def choose_ride_like_browser(self):
        """
        Exact browser behaviour:
        - GET request
        - Query parameters
        - Correct passenger URL
        """
        self.client.get(
            "/passenger/choose-ride/",
            params={
                "pickup": "Andheri",
                "dropoff": "Bandra",
                "ride_type": "daily",
                "distance_km": 7.5,
                "duration_min": 18
            },
            name="GET /passenger/choose-ride/"
        )