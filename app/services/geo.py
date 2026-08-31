from sqlalchemy import func

EARTH_RADIUS_KM = 6371.0


def haversine_km_expr(lat_col, lng_col, lat: float, lng: float):
    """SQL expression computing great-circle distance (km) between a row's
    coordinates and a fixed point, using the haversine formula."""
    lat1 = func.radians(lat)
    lat2 = func.radians(lat_col)
    dlat = lat2 - lat1
    dlng = func.radians(lng_col) - func.radians(lng)

    a = func.pow(func.sin(dlat / 2), 2) + func.cos(lat1) * func.cos(lat2) * func.pow(func.sin(dlng / 2), 2)
    c = 2 * func.asin(func.sqrt(a))
    return EARTH_RADIUS_KM * c
