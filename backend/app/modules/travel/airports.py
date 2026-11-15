"""Commercial airports of Vietnam, used to pick the airport nearest to a place.

Coordinates are approximate (about 1 km), which is enough to choose an airport.
Places outside Vietnam need the IATA code entered by the user.
"""

from dataclasses import dataclass

from app.infrastructure.geo import GeoPoint, distance_km


@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    lat: float
    lon: float


AIRPORTS: tuple[Airport, ...] = (
    Airport("HAN", "Nội Bài", "Hà Nội", 21.221, 105.807),
    Airport("SGN", "Tân Sơn Nhất", "TP. Hồ Chí Minh", 10.819, 106.652),
    Airport("DAD", "Đà Nẵng", "Đà Nẵng", 16.044, 108.199),
    Airport("CXR", "Cam Ranh", "Nha Trang", 11.998, 109.219),
    Airport("PQC", "Phú Quốc", "Phú Quốc", 10.170, 103.993),
    Airport("HPH", "Cát Bi", "Hải Phòng", 20.819, 106.725),
    Airport("HUI", "Phú Bài", "Huế", 16.402, 107.703),
    Airport("VII", "Vinh", "Vinh", 18.738, 105.671),
    Airport("DLI", "Liên Khương", "Đà Lạt", 11.750, 108.367),
    Airport("UIH", "Phù Cát", "Quy Nhơn", 13.955, 109.042),
    Airport("BMV", "Buôn Ma Thuột", "Buôn Ma Thuột", 12.668, 108.120),
    Airport("VCA", "Cần Thơ", "Cần Thơ", 10.085, 105.712),
    Airport("VDO", "Vân Đồn", "Quảng Ninh", 21.118, 107.414),
    Airport("THD", "Thọ Xuân", "Thanh Hóa", 19.902, 105.468),
    Airport("VDH", "Đồng Hới", "Quảng Bình", 17.515, 106.591),
    Airport("VCL", "Chu Lai", "Quảng Nam", 15.403, 108.706),
    Airport("TBB", "Tuy Hòa", "Phú Yên", 13.050, 109.334),
    Airport("PXU", "Pleiku", "Gia Lai", 14.005, 108.017),
    Airport("DIN", "Điện Biên Phủ", "Điện Biên", 21.398, 103.008),
    Airport("VCS", "Côn Đảo", "Côn Đảo", 8.732, 106.633),
    Airport("CAH", "Cà Mau", "Cà Mau", 9.178, 105.178),
    Airport("VKG", "Rạch Giá", "Rạch Giá", 9.958, 105.132),
)

# Beyond this distance an airport is not a practical way to reach a place.
MAX_AIRPORT_DISTANCE_KM = 150.0


def nearest_airport(point: GeoPoint, *, max_km: float = MAX_AIRPORT_DISTANCE_KM) -> Airport | None:
    best: Airport | None = None
    best_distance = max_km
    for airport in AIRPORTS:
        distance = distance_km(point, GeoPoint(lat=airport.lat, lon=airport.lon))
        if distance <= best_distance:
            best, best_distance = airport, distance
    return best


def find_airport(code: str) -> Airport | None:
    wanted = code.strip().upper()
    return next((airport for airport in AIRPORTS if airport.code == wanted), None)
