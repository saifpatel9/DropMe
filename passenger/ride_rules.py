from decimal import Decimal, InvalidOperation
from django.conf import settings


def normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def get_outstation_threshold_km() -> Decimal:
    return Decimal(str(getattr(settings, "OUTSTATION_DISTANCE_KM", 40)))


def get_outstation_disallowed() -> list:
    return list(getattr(settings, "OUTSTATION_DISALLOWED_VEHICLES", ["Bike", "Auto"]))


def parse_decimal(value):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def build_meta(city=None, district=None, state=None):
    return {
        "city": city or "",
        "district": district or "",
        "state": state or "",
    }


def get_primary_locality(meta) -> str:
    return (meta.get("city") or meta.get("district") or "").strip()


def is_daily_allowed(pickup_meta, drop_meta, allowed_cities=None, allowed_states=None):
    if not pickup_meta or not drop_meta:
        return {"allowed": None, "reason": "missing"}

    pickup_city = normalize_text(get_primary_locality(pickup_meta))
    drop_city = normalize_text(get_primary_locality(drop_meta))
    pickup_state = normalize_text(pickup_meta.get("state"))
    drop_state = normalize_text(drop_meta.get("state"))

    if not pickup_city or not drop_city or not pickup_state or not drop_state:
        return {"allowed": None, "reason": "incomplete"}

    same_city = pickup_city == drop_city and pickup_state == drop_state

    allowed_cities = [normalize_text(c) for c in (allowed_cities or []) if c]
    allowed_states = [normalize_text(s) for s in (allowed_states or []) if s]
    both_in_allowed_cities = (
        allowed_cities
        and pickup_city in allowed_cities
        and drop_city in allowed_cities
    )
    same_allowed_state = (
        allowed_states
        and pickup_state == drop_state
        and pickup_state in allowed_states
    )

    return {"allowed": same_city or both_in_allowed_cities or same_allowed_state, "reason": "boundary"}


def derive_ride_type(requested_type, pickup_meta, drop_meta, distance_km, threshold_km=None, allowed_cities=None, allowed_states=None):
    requested = normalize_text(requested_type)
    if requested == "rental":
        return {"ride_type": "rental", "reason": "requested"}

    threshold = threshold_km if threshold_km is not None else get_outstation_threshold_km()
    if distance_km is not None and distance_km >= threshold:
        return {"ride_type": "outstation", "reason": "distance"}

    decision = is_daily_allowed(pickup_meta, drop_meta, allowed_cities, allowed_states)
    if decision["allowed"] is True:
        return {"ride_type": "daily", "reason": "locality"}
    if decision["allowed"] is False:
        return {"ride_type": "outstation", "reason": "locality"}

    # Fallback when we cannot infer (keep explicit outstation requests)
    if requested == "outstation":
        return {"ride_type": "outstation", "reason": "requested"}
    return {"ride_type": "daily", "reason": "fallback"}


def is_vehicle_allowed(ride_type, service_name):
    if normalize_text(ride_type) != "outstation":
        return True
    disallowed = [normalize_text(v) for v in get_outstation_disallowed()]
    return normalize_text(service_name) not in disallowed
