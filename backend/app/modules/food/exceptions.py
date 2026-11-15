from app.core.exceptions import ValidationFailedError


class InvalidDishQueryError(ValidationFailedError):
    code = "invalid_dish_query"
    message = "Tên món ăn chỉ gồm chữ, số, khoảng trắng và dấu gạch ngang."


class FoodPlaceNotFoundError(ValidationFailedError):
    code = "place_not_found"
    message = "Không tìm thấy địa điểm."
