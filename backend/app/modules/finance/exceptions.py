from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationFailedError,
)


class CategoryNotFoundError(NotFoundError):
    code = "category_not_found"
    message = "Không tìm thấy danh mục."


class TransactionNotFoundError(NotFoundError):
    code = "transaction_not_found"
    message = "Không tìm thấy giao dịch."


class BudgetNotFoundError(NotFoundError):
    code = "budget_not_found"
    message = "Không tìm thấy ngân sách."


class CategoryNameTakenError(ConflictError):
    code = "category_name_taken"
    message = "Đã có danh mục cùng tên và cùng loại."


class CategoryInUseError(ConflictError):
    code = "category_in_use"
    message = "Danh mục đang được dùng trong giao dịch hoặc ngân sách nên không thể xóa."


class BudgetExistsError(ConflictError):
    code = "budget_exists"
    message = "Tháng này đã có ngân sách cho mục đó. Hãy sửa ngân sách hiện có."


class InvalidAmountError(ValidationFailedError):
    code = "invalid_amount"
    message = "Số tiền không hợp lệ."


class CategoryKindMismatchError(BusinessRuleError):
    code = "category_kind_mismatch"
    message = "Danh mục không cùng loại với giao dịch."
