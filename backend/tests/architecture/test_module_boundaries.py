"""Enforce the dependency rules described in docs/architecture.

The rules are checked by reading import statements, so a violation fails the
test suite as soon as it is written.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
MODULES_ROOT = APP_ROOT / "modules"

# Business modules the AI core must never know about.
BUSINESS_MODULES = frozenset({"finance", "travel", "food", "dashboard"})


@dataclass(frozen=True)
class ImportedName:
    source: Path
    module: str

    def __str__(self) -> str:
        return f"{self.source.relative_to(APP_ROOT.parent).as_posix()} imports {self.module}"


def _imports(path: Path) -> list[ImportedName]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[ImportedName] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(ImportedName(path, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append(ImportedName(path, node.module))
    return found


def _all_imports(root: Path) -> list[ImportedName]:
    return [imported for path in sorted(root.rglob("*.py")) for imported in _imports(path)]


def _owning_module(path: Path) -> str:
    return path.relative_to(MODULES_ROOT).parts[0]


def test_source_tree_is_discovered() -> None:
    # Guards against the checks below passing only because nothing was scanned.
    assert _all_imports(MODULES_ROOT), "no imports found under app/modules"


def test_modules_import_other_modules_only_through_public() -> None:
    violations = []
    for imported in _all_imports(MODULES_ROOT):
        parts = imported.module.split(".")
        if parts[:2] != ["app", "modules"] or len(parts) < 3:
            continue
        target = parts[2]
        if target == _owning_module(imported.source):
            continue
        if parts[3:] != ["public"]:
            violations.append(str(imported))

    assert not violations, "Cross-module imports must target `<module>.public`:\n" + "\n".join(
        violations
    )


def test_ai_core_does_not_import_business_modules() -> None:
    ai_root = MODULES_ROOT / "ai"
    violations = [
        str(imported)
        for imported in (_all_imports(ai_root) if ai_root.exists() else [])
        if imported.module.split(".")[:2] == ["app", "modules"]
        and imported.module.split(".")[2:3]
        and imported.module.split(".")[2] in BUSINESS_MODULES
    ]

    assert not violations, "AI core must not depend on business modules:\n" + "\n".join(violations)


def test_core_shared_and_infrastructure_do_not_import_modules() -> None:
    violations = [
        str(imported)
        for package in ("core", "shared", "infrastructure")
        if (APP_ROOT / package).exists()
        for imported in _all_imports(APP_ROOT / package)
        # The model registry exists precisely to import every module's models.
        if imported.source.name != "models.py"
        and imported.module.split(".")[:2] == ["app", "modules"]
    ]

    assert not violations, "Lower layers must not depend on modules:\n" + "\n".join(violations)


def test_services_do_not_depend_on_the_web_framework() -> None:
    violations = [
        str(imported)
        for path in sorted(MODULES_ROOT.rglob("service.py"))
        for imported in _imports(path)
        if imported.module.split(".")[0] in {"fastapi", "starlette"}
    ]

    assert not violations, "Services must be independent of HTTP:\n" + "\n".join(violations)
