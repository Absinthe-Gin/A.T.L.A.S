from app.core.exceptions import BusinessRuleError, NotFoundError


class TravelPlanNotFoundError(NotFoundError):
    code = "travel_plan_not_found"
    message = "Không tìm thấy kế hoạch du lịch."


class ItineraryItemNotFoundError(NotFoundError):
    code = "itinerary_item_not_found"
    message = "Không tìm thấy mục trong lịch trình."


class InvalidDateRangeError(BusinessRuleError):
    code = "invalid_date_range"
    message = "Ngày về không được trước ngày đi."


class DayOutsidePlanError(BusinessRuleError):
    code = "day_outside_plan"
    message = "Ngày của hoạt động nằm ngoài thời gian chuyến đi."


class PlaceNotFoundError(NotFoundError):
    code = "place_not_found"
    message = "Không tìm thấy địa điểm phù hợp."
