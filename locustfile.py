import itertools
import os
import random
import re
from typing import List, Optional, Tuple

from locust import HttpUser, LoadTestShape, between, task


CSRF_RE = re.compile(r"name=['\"]csrfmiddlewaretoken['\"]\s+value=['\"]([^'\"]+)['\"]")


# ----------------------------
# Config helpers
# ----------------------------
def _parse_credential_list(raw: str) -> List[Tuple[str, str]]:
    """
    Parse credentials in the form: email1:pass1,email2:pass2
    """
    creds: List[Tuple[str, str]] = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        email, password = part.split(":", 1)
        email = email.strip()
        password = password.strip()
        if email and password:
            creds.append((email, password))
    return creds


def _credential_pool(list_env: str, email_env: str, password_env: str) -> List[Tuple[str, str]]:
    listed = _parse_credential_list(os.getenv(list_env, ""))
    if listed:
        return listed

    email = os.getenv(email_env, "").strip()
    password = os.getenv(password_env, "").strip()
    if email and password:
        return [(email, password)]

    return []


PASSENGER_CREDS = _credential_pool("PASSENGER_CREDENTIALS", "PASSENGER_EMAIL", "PASSENGER_PASSWORD")
DRIVER_CREDS = _credential_pool("DRIVER_CREDENTIALS", "DRIVER_EMAIL", "DRIVER_PASSWORD")
ADMIN_CREDS = _credential_pool("ADMIN_CREDENTIALS", "ADMIN_EMAIL", "ADMIN_PASSWORD")

PASSENGER_CYCLE = itertools.cycle(PASSENGER_CREDS) if PASSENGER_CREDS else None
DRIVER_CYCLE = itertools.cycle(DRIVER_CREDS) if DRIVER_CREDS else None
ADMIN_CYCLE = itertools.cycle(ADMIN_CREDS) if ADMIN_CREDS else None


# Reusable route samples for realistic ride discovery/booking browsing
ROUTE_SAMPLES = [
    {
        "pickup": "Andheri East, Mumbai",
        "dropoff": "Bandra West, Mumbai",
        "pickup_lat": "19.1136",
        "pickup_lng": "72.8697",
        "drop_lat": "19.0596",
        "drop_lng": "72.8295",
        "pickup_city": "Mumbai",
        "pickup_district": "Mumbai Suburban",
        "pickup_state": "Maharashtra",
        "drop_city": "Mumbai",
        "drop_district": "Mumbai Suburban",
        "drop_state": "Maharashtra",
        "distance_km": "7.5",
        "duration_min": "18",
    },
    {
        "pickup": "Hinjewadi Phase 1, Pune",
        "dropoff": "Koregaon Park, Pune",
        "pickup_lat": "18.5912",
        "pickup_lng": "73.7389",
        "drop_lat": "18.5362",
        "drop_lng": "73.8957",
        "pickup_city": "Pune",
        "pickup_district": "Pune",
        "pickup_state": "Maharashtra",
        "drop_city": "Pune",
        "drop_district": "Pune",
        "drop_state": "Maharashtra",
        "distance_km": "16.2",
        "duration_min": "36",
    },
    {
        "pickup": "Whitefield, Bengaluru",
        "dropoff": "Koramangala, Bengaluru",
        "pickup_lat": "12.9698",
        "pickup_lng": "77.7500",
        "drop_lat": "12.9352",
        "drop_lng": "77.6245",
        "pickup_city": "Bengaluru",
        "pickup_district": "Bengaluru Urban",
        "pickup_state": "Karnataka",
        "drop_city": "Bengaluru",
        "drop_district": "Bengaluru Urban",
        "drop_state": "Karnataka",
        "distance_km": "14.4",
        "duration_min": "34",
    },
]

VEHICLE_TYPES = ["Hatchback", "Sedan", "SUV", "Auto", "Bike"]
RIDE_TYPES = ["daily", "daily", "daily", "rental", "outstation"]
ENABLE_CONFIRM_BOOKING = os.getenv("ENABLE_CONFIRM_BOOKING", "0").strip().lower() in {"1", "true", "yes"}


# ----------------------------
# Base helpers
# ----------------------------
class BaseCabUser(HttpUser):
    abstract = True
    wait_time = between(1, 6)

    def _csrf_from_response(self, response) -> Optional[str]:
        token = response.cookies.get("csrftoken")
        if token:
            return token

        match = CSRF_RE.search(response.text or "")
        if match:
            return match.group(1)

        token = self.client.cookies.get("csrftoken")
        return token

    def _get_csrf_token(self, path: str, request_name: Optional[str] = None) -> Optional[str]:
        resp = self.client.get(path, name=request_name or f"GET {path}")
        return self._csrf_from_response(resp)

    def _login_post(self, login_path: str, email: str, password: str, request_name: str) -> bool:
        token = self._get_csrf_token(login_path, request_name=f"GET {login_path} [csrf]")
        if not token:
            return False

        payload = {
            "email": email,
            "password": password,
            "csrfmiddlewaretoken": token,
        }
        headers = {"Referer": f"{self.host}{login_path}"}

        with self.client.post(
            login_path,
            data=payload,
            headers=headers,
            name=request_name,
            allow_redirects=True,
            catch_response=True,
        ) as resp:
            text = (resp.text or "").lower()
            if resp.status_code >= 500:
                resp.failure(f"Server error during login: {resp.status_code}")
                return False

            if "invalid email or password" in text or "invalid password" in text or "invalid email" in text:
                resp.failure("Invalid credentials")
                return False

            resp.success()
            return True

    def _protected_get(self, path: str, request_name: Optional[str] = None):
        """
        Access a protected page and treat redirect-to-login as failure.
        """
        with self.client.get(path, name=request_name or f"GET {path}", allow_redirects=False, catch_response=True) as resp:
            location = (resp.headers.get("Location") or "").lower()
            if resp.status_code in (301, 302) and "login" in location:
                resp.failure(f"Unauthorized redirect for {path}")
                return
            if resp.status_code >= 400:
                resp.failure(f"HTTP {resp.status_code} for {path}")
                return
            resp.success()

    def _logout(self):
        self.client.get("/logout/", name="GET /logout/")


# ----------------------------
# User models / scenarios
# ----------------------------
class PassengerAnonymousUser(BaseCabUser):
    """
    Unauthenticated browsing traffic (landing + browse-heavy).
    """

    weight = 4

    @task(4)
    def homepage(self):
        self.client.get("/passenger/cab-homepage/", name="GET /passenger/cab-homepage/")

    @task(3)
    def faq(self):
        self.client.get("/passenger/faq/", name="GET /passenger/faq/")

    @task(3)
    def ride_discovery(self):
        route = random.choice(ROUTE_SAMPLES)
        params = {
            "pickup": route["pickup"],
            "dropoff": route["dropoff"],
            "pickup_city": route["pickup_city"],
            "pickup_district": route["pickup_district"],
            "pickup_state": route["pickup_state"],
            "drop_city": route["drop_city"],
            "drop_district": route["drop_district"],
            "drop_state": route["drop_state"],
            "pickup_lat": route["pickup_lat"],
            "pickup_lng": route["pickup_lng"],
            "drop_lat": route["drop_lat"],
            "drop_lng": route["drop_lng"],
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "ride_type": random.choice(RIDE_TYPES),
        }
        self.client.get("/passenger/choose-ride/", params=params, name="GET /passenger/choose-ride/")


class PassengerAuthenticatedUser(BaseCabUser):
    """
    Logged-in passenger journey with weighted navigation and light booking flow.
    """

    weight = 8
    _logged_in = False

    def on_start(self):
        self._logged_in = self._login()

    def on_stop(self):
        if self._logged_in:
            self._logout()

    def _login(self) -> bool:
        if not PASSENGER_CYCLE:
            return False
        email, password = next(PASSENGER_CYCLE)
        ok = self._login_post("/login/", email, password, request_name="POST /login/ [passenger]")
        if ok:
            self._protected_get("/passenger/cab-homepage/", request_name="GET /passenger/cab-homepage/ [auth-check]")
        return ok

    def _ensure_session(self):
        if not self._logged_in:
            self._logged_in = self._login()

    @task(4)
    def dashboard_and_profile(self):
        self._ensure_session()
        self._protected_get("/passenger/cab-homepage/", request_name="GET /passenger/cab-homepage/ [auth]")
        self._protected_get("/passenger/profile/", request_name="GET /passenger/profile/")

    @task(3)
    def my_rides_and_sections(self):
        self._ensure_session()
        self._protected_get("/passenger/profile/section/my-rides/", request_name="GET /passenger/profile/section/my-rides/")
        self._protected_get("/passenger/profile/section/payment/", request_name="GET /passenger/profile/section/payment/")

    @task(2)
    def ride_discovery(self):
        self._ensure_session()
        route = random.choice(ROUTE_SAMPLES)
        params = {
            "pickup": route["pickup"],
            "dropoff": route["dropoff"],
            "pickup_city": route["pickup_city"],
            "pickup_district": route["pickup_district"],
            "pickup_state": route["pickup_state"],
            "drop_city": route["drop_city"],
            "drop_district": route["drop_district"],
            "drop_state": route["drop_state"],
            "pickup_lat": route["pickup_lat"],
            "pickup_lng": route["pickup_lng"],
            "drop_lat": route["drop_lat"],
            "drop_lng": route["drop_lng"],
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "ride_type": random.choice(RIDE_TYPES),
        }
        self.client.get("/passenger/choose-ride/", params=params, name="GET /passenger/choose-ride/ [auth]")

    @task(2)
    def booking_intent_browse(self):
        """
        Lightweight booking flow simulation without forcing full POST confirm.
        This still exercises booking page rendering and session writes.
        """
        self._ensure_session()
        route = random.choice(ROUTE_SAMPLES)
        params = {
            "pickup": route["pickup"],
            "dropoff": route["dropoff"],
            "service_name": random.choice(VEHICLE_TYPES),
            "fare": str(random.randint(120, 780)),
            "ride_type": random.choice(RIDE_TYPES),
            "pickup_city": route["pickup_city"],
            "pickup_district": route["pickup_district"],
            "pickup_state": route["pickup_state"],
            "drop_city": route["drop_city"],
            "drop_district": route["drop_district"],
            "drop_state": route["drop_state"],
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "pickup_lat": route["pickup_lat"],
            "pickup_lng": route["pickup_lng"],
            "drop_lat": route["drop_lat"],
            "drop_lng": route["drop_lng"],
        }
        self._protected_get("/passenger/book-ride/", request_name="GET /passenger/book-ride/ [warm]")
        self.client.get("/passenger/book-ride/", params=params, name="GET /passenger/book-ride/")

    @task(1)
    def relogin_cycle(self):
        self._ensure_session()
        self._logout()
        self._logged_in = self._login()

    @task(1)
    def confirm_booking_optional(self):
        """
        Optional end-to-end booking POST.
        Disabled by default to avoid creating large test data unless explicitly requested.
        """
        if not ENABLE_CONFIRM_BOOKING:
            return

        self._ensure_session()
        route = random.choice(ROUTE_SAMPLES)
        vehicle = os.getenv("BOOKING_VEHICLE_TYPE", random.choice(VEHICLE_TYPES))

        warm_params = {
            "pickup": route["pickup"],
            "dropoff": route["dropoff"],
            "service_name": vehicle,
            "fare": str(random.randint(120, 780)),
            "ride_type": random.choice(RIDE_TYPES),
            "pickup_city": route["pickup_city"],
            "pickup_district": route["pickup_district"],
            "pickup_state": route["pickup_state"],
            "drop_city": route["drop_city"],
            "drop_district": route["drop_district"],
            "drop_state": route["drop_state"],
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "pickup_lat": route["pickup_lat"],
            "pickup_lng": route["pickup_lng"],
            "drop_lat": route["drop_lat"],
            "drop_lng": route["drop_lng"],
        }
        token = self._get_csrf_token(
            "/passenger/book-ride/",
            request_name="GET /passenger/book-ride/ [csrf]",
        )
        self.client.get("/passenger/book-ride/", params=warm_params, name="GET /passenger/book-ride/ [confirm-flow]")
        token = token or self.client.cookies.get("csrftoken")
        if not token:
            return

        payload = {
            "vehicle_type": vehicle,
            "pickup": route["pickup"],
            "dropoff": route["dropoff"],
            "fare": str(random.randint(120, 780)),
            "ride_date": "",
            "ride_time": "",
            "ride_type": "daily",
            "pickup_city": route["pickup_city"],
            "pickup_district": route["pickup_district"],
            "pickup_state": route["pickup_state"],
            "drop_city": route["drop_city"],
            "drop_district": route["drop_district"],
            "drop_state": route["drop_state"],
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "pickup_lat": route["pickup_lat"],
            "pickup_lng": route["pickup_lng"],
            "drop_lat": route["drop_lat"],
            "drop_lng": route["drop_lng"],
            "payment_mode": random.choice(["Cash", "UPI", "Wallet"]),
            "csrfmiddlewaretoken": token,
        }
        headers = {"Referer": f"{self.host}/passenger/book-ride/"}
        self.client.post(
            "/passenger/confirm-booking/",
            data=payload,
            headers=headers,
            allow_redirects=True,
            name="POST /passenger/confirm-booking/",
        )


class DriverAuthenticatedUser(BaseCabUser):
    """
    Driver portal activity (light-to-moderate usage).
    """

    weight = 3
    _logged_in = False

    def on_start(self):
        self._logged_in = self._login()

    def on_stop(self):
        if self._logged_in:
            self._logout()

    def _login(self) -> bool:
        if not DRIVER_CYCLE:
            return False
        email, password = next(DRIVER_CYCLE)
        ok = self._login_post("/login/", email, password, request_name="POST /login/ [driver]")
        if ok:
            self._protected_get("/driver/driver_homepage/", request_name="GET /driver/driver_homepage/ [auth-check]")
        return ok

    def _ensure_session(self):
        if not self._logged_in:
            self._logged_in = self._login()

    @task(4)
    def driver_dashboard(self):
        self._ensure_session()
        self._protected_get("/driver/driver_homepage/", request_name="GET /driver/driver_homepage/")

    @task(3)
    def assignment_apis(self):
        self._ensure_session()
        self._protected_get("/driver/api/assigned-requests/", request_name="GET /driver/api/assigned-requests/")
        self._protected_get("/driver/api/active-booking/", request_name="GET /driver/api/active-booking/")

    @task(2)
    def rides_and_earnings(self):
        self._ensure_session()
        self._protected_get("/driver/rides/", request_name="GET /driver/rides/")
        self._protected_get("/driver/driver/earnings/", request_name="GET /driver/driver/earnings/")

    @task(1)
    def profile(self):
        self._ensure_session()
        self._protected_get("/driver/driver/profile/", request_name="GET /driver/driver/profile/")


class AdminLightUser(BaseCabUser):
    """
    Low-volume admin interactions for control-plane load.
    """

    weight = 1
    _logged_in = False

    def on_start(self):
        self._logged_in = self._login()

    def on_stop(self):
        if self._logged_in:
            self._logout()

    def _login(self) -> bool:
        if not ADMIN_CYCLE:
            return False
        email, password = next(ADMIN_CYCLE)
        ok = self._login_post("/panel/login/", email, password, request_name="POST /panel/login/")
        if ok:
            self._protected_get("/panel/", request_name="GET /panel/ [auth-check]")
        return ok

    def _ensure_session(self):
        if not self._logged_in:
            self._logged_in = self._login()

    @task(4)
    def dashboard(self):
        self._ensure_session()
        self._protected_get("/panel/", request_name="GET /panel/")

    @task(2)
    def passengers(self):
        self._ensure_session()
        self._protected_get("/panel/passengers/", request_name="GET /panel/passengers/")

    @task(2)
    def drivers(self):
        self._ensure_session()
        self._protected_get("/panel/drivers/", request_name="GET /panel/drivers/")

    @task(1)
    def bookings(self):
        self._ensure_session()
        self._protected_get("/panel/bookings/", request_name="GET /panel/bookings/")


class RandomNavigationUser(BaseCabUser):
    """
    Random clicks across commonly reachable pages.
    """

    weight = 2

    @task
    def random_nav(self):
        candidates = [
            "/",
            "/passenger/cab-homepage/",
            "/passenger/faq/",
            "/passenger/choose-ride/",
            "/login/",
            "/panel/login/",
        ]
        path = random.choice(candidates)
        self.client.get(path, name=f"GET {path}")


# ----------------------------
# Optional staged load shape
# ----------------------------
class StagedLoadShape(LoadTestShape):
    """
    Use env var LOAD_PROFILE to pick a scenario: light, moderate, heavy, stress.
    Example:
      LOAD_PROFILE=heavy locust -f locustfile.py --host http://127.0.0.1:8000 --headless -t 20m
    """

    profile = os.getenv("LOAD_PROFILE", "").strip().lower()

    _profiles = {
        "light": [
            {"duration": 60 * 5, "users": 50, "spawn_rate": 2},
        ],
        "moderate": [
            {"duration": 60 * 10, "users": 200, "spawn_rate": 5},
        ],
        "heavy": [
            {"duration": 60 * 5, "users": 300, "spawn_rate": 10},
            {"duration": 60 * 10, "users": 600, "spawn_rate": 15},
            {"duration": 60 * 20, "users": 1000, "spawn_rate": 20},
        ],
    }

    def tick(self):
        if not self.profile:
            return None

        run_time = self.get_run_time()

        if self.profile == "stress":
            # Increase by step every window until max users.
            window_seconds = int(os.getenv("STRESS_STEP_SECONDS", "180"))
            step_users = int(os.getenv("STRESS_STEP_USERS", "100"))
            spawn_rate = float(os.getenv("STRESS_SPAWN_RATE", "15"))
            max_users = int(os.getenv("STRESS_MAX_USERS", "2000"))

            current_users = min(((run_time // window_seconds) + 1) * step_users, max_users)
            return int(current_users), spawn_rate

        stages = self._profiles.get(self.profile)
        if not stages:
            return None

        for stage in stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None
