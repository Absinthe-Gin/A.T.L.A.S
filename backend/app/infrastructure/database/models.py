"""Model registry.

Importing this module loads every ORM model so that ``Base.metadata`` is
complete. Alembic and tests rely on it. It is the only place outside a module
that may import that module's ``models``.
"""

from app.modules.ai import models as ai_models
from app.modules.finance import models as finance_models
from app.modules.memory import models as memory_models
from app.modules.travel import models as travel_models
from app.modules.users import models as users_models

__all__ = ["ai_models", "finance_models", "memory_models", "travel_models", "users_models"]
