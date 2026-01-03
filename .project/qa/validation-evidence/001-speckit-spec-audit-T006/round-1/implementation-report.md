---
taskId: T006
round: 1
completionStatus: complete
tddCompliance:
  redPhase: Tests written first in backend/tests/test_core_settings.py
  greenPhase: Implementation added to backend/core/settings.py
  refactorPhase: Code uses pydantic BeforeValidator for clean parsing
---

# T006 Implementation Report: Project Discovery Configuration

## Summary

Established project discovery configuration in the Settings class, adding:
- `scan_roots` - Directories to scan for Edison projects
- `scan_ignore_patterns` - Patterns to ignore during scanning
- `pin_storage_path` - Path to store pinned projects

## Files Modified

### `/Users/leeroy/Documents/Development/edison-ui/backend/core/settings.py`

Added project discovery configuration fields with proper pydantic-settings v2 patterns:

```python
from typing import Annotated
from pydantic import BeforeValidator

def _parse_comma_separated(value: str | list[str]) -> list[str]:
    """Parse a comma-separated string into a list."""
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

CommaSeparatedList = Annotated[list[str], BeforeValidator(_parse_comma_separated)]

class Settings(BaseSettings):
    # ... existing fields ...

    # Project discovery configuration (T006)
    scan_roots: CommaSeparatedList = ["~/projects"]
    scan_ignore_patterns: CommaSeparatedList = [
        "node_modules",
        ".git",
        ".venv",
        "__pycache__",
    ]
    pin_storage_path: str = "~/.edison-ui/pins.json"

    def get_expanded_scan_roots(self) -> list[str]:
        """Return scan_roots with tilde expanded to absolute paths."""
        return [str(Path(root).expanduser().resolve()) for root in self.scan_roots]

    def get_expanded_pin_storage_path(self) -> str | None:
        """Return pin_storage_path with tilde expanded."""
        if not self.pin_storage_path:
            return None
        return str(Path(self.pin_storage_path).expanduser().resolve())
```

### `/Users/leeroy/Documents/Development/edison-ui/backend/tests/test_core_settings.py`

Added comprehensive test suite with 15 test cases covering:

1. **TestScanRootsConfig** (5 tests)
   - Default value is `["~/projects"]`
   - Single path from SCAN_ROOTS env var
   - Comma-separated multiple paths from SCAN_ROOTS
   - Tilde expansion works correctly
   - Expansion preserves order

2. **TestScanIgnorePatternsConfig** (3 tests)
   - Default patterns include node_modules, .git, .venv, __pycache__
   - Loading from SCAN_IGNORE_PATTERNS env var
   - Empty string results in empty list

3. **TestPinStoragePathConfig** (4 tests)
   - Default value is `~/.edison-ui/pins.json`
   - Loading from PIN_STORAGE_PATH env var
   - Empty value handling
   - Tilde expansion in get_expanded_pin_storage_path()

4. **TestExistingSettingsPreserved** (5 tests)
   - api_host still works
   - api_port still works
   - cors_origins still works
   - edison_path still accessible
   - edison_projects_root still accessible

## TDD Compliance

### RED Phase
- Tests written first defining expected behavior
- Tests use `patch.dict(os.environ, ...)` to test env var loading
- Tests verify tilde expansion with `Path.home()`

### GREEN Phase
- `CommaSeparatedList` type alias with `BeforeValidator` for parsing
- Helper methods for path expansion
- All fields use proper defaults

### REFACTOR Phase
- Clean separation of parsing logic into `_parse_comma_separated()`
- Type-safe with `Annotated` type hints
- Consistent with pydantic-settings v2 patterns

## Environment Variable Mapping

| Setting | Env Var | Format | Default |
|---------|---------|--------|---------|
| scan_roots | SCAN_ROOTS | Comma-separated | ~/projects |
| scan_ignore_patterns | SCAN_IGNORE_PATTERNS | Comma-separated | node_modules,.git,.venv,__pycache__ |
| pin_storage_path | PIN_STORAGE_PATH | String path | ~/.edison-ui/pins.json |

## Verification Commands

```bash
# Run tests
make backend-test

# Run specific test file
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/test_core_settings.py -v

# Type check
make backend-lint
```

## Notes

- Uses pydantic-settings v2 `BeforeValidator` for clean comma-separated parsing
- Path expansion is lazy (via methods) to avoid issues during settings instantiation
- Existing settings (api_host, api_port, cors_origins, etc.) are preserved and functional
