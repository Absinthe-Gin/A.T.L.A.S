"""Model registry.

Importing this module loads every ORM model so that ``Base.metadata`` is
complete. Alembic and tests rely on it. It is the only place outside a module
that may import that module's ``models``.
"""

from app.modules.memory import models as memory_models
from app.modules.users import models as users_models

__all__ = ["memory_models", "users_models"]
