"""Regional specialties: the editorial suggestions Atlas shows for each region.

These are NOT statistics. They are a short list written for this app. Each dish
is searched by the `search_terms` below in OpenStreetMap, so a dish only shows
restaurants that are mapped with that dish in their name.
"""

from dataclasses import dataclass

from app.infrastructure.geo import GeoPoint


@dataclass(frozen=True)
class Dish:
    name: str
    description: str
    search_terms: tuple[str, ...]


@dataclass(frozen=True)
class Region:
    key: str
    name: str
    reference_city: str
    center: GeoPoint
    dishes: tuple[Dish, ...]


REGIONS: tuple[Region, ...] = (
    Region(
        key="north",
        name="Miền Bắc",
        reference_city="Hà Nội",
        center=GeoPoint(lat=21.0285, lon=105.8542),
        dishes=(
            Dish("Phở bò", "Nước dùng trong, thường ăn sáng.", ("phở", "pho")),
            Dish(
                "Bún chả",
                "Chả thịt nướng than ăn cùng bún và nước chấm chua ngọt.",
                ("bún chả", "bun cha"),
            ),
            Dish(
                "Chả cá", "Cá nướng với thì là và mẻ, món đặc trưng Hà Nội.", ("chả cá", "cha ca")
            ),
            Dish("Bún thang", "Bún với gà, trứng thái sợi và mắm tôm.", ("bún thang", "bun thang")),
        ),
    ),
    Region(
        key="central",
        name="Miền Trung",
        reference_city="Đà Nẵng",
        center=GeoPoint(lat=16.0544, lon=108.2022),
        dishes=(
            Dish("Bún bò Huế", "Nước dùng cay sả, ăn với chả và giò heo.", ("bún bò", "bun bo")),
            Dish(
                "Mì Quảng",
                "Mì sợi bản rộng ít nước dùng, ăn kèm rau và đậu phộng.",
                ("mì quảng", "mi quang"),
            ),
            Dish(
                "Cao lầu", "Mì Hội An dai, dùng với thịt heo và rau sống.", ("cao lầu", "cao lau")
            ),
            Dish(
                "Bánh bèo",
                "Bánh hấp nhỏ trong chén, rắc tôm chấy và mỡ hành.",
                ("bánh bèo", "banh beo"),
            ),
        ),
    ),
    Region(
        key="south",
        name="Miền Nam",
        reference_city="TP. Hồ Chí Minh",
        center=GeoPoint(lat=10.7769, lon=106.7009),
        dishes=(
            Dish(
                "Hủ tiếu",
                "Hủ tiếu Nam Vang với tôm, thịt và nước dùng ngọt.",
                ("hủ tiếu", "hu tieu"),
            ),
            Dish("Cơm tấm", "Sườn nướng ăn với cơm tấm và bì chả.", ("cơm tấm", "com tam")),
            Dish("Bánh xèo", "Bánh giòn nhân tôm thịt, cuốn rau.", ("bánh xèo", "banh xeo")),
            Dish(
                "Lẩu mắm",
                "Lẩu với mắm, nhiều rau đồng, đặc trưng miền Tây.",
                ("lẩu mắm", "lau mam"),
            ),
        ),
    ),
)
