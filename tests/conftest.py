"""Root conftest: isolate tests from real .env and external services.

Two production-level issues prevent tests from running without this conftest:

1. config.py: `settings = Settings()` runs at import time. The real .env has
   infra-only keys (GRAFANA_*, PREFECT_API_URL, SLACK_BOT_TOKEN, SENTRY_DSN)
   not declared in the Settings model. pydantic-settings defaults to
   extra='forbid', so the import raises a ValidationError.

2. logger.py: `configure_logging()` runs at import time and sets up structlog
   with `PrintLoggerFactory()` + `add_logger_name` processor. `add_logger_name`
   calls `logger.name` which only exists on stdlib loggers, not PrintLogger,
   raising AttributeError on every log call.

Both are production bugs (reported below). Fix in the test layer: inject safe
stub modules into sys.modules inside pytest_configure, which runs before any
test module is imported.
"""

import logging
import sys
import types
from unittest.mock import MagicMock


def _make_settings_module() -> types.ModuleType:
    """Return a fake quant_alpha.common.config module with a safe settings stub."""
    fake_settings = MagicMock()
    fake_settings.postgres_user = "quant"
    fake_settings.postgres_password = ""
    fake_settings.postgres_db = "quant_db"
    fake_settings.postgres_host = "localhost"
    fake_settings.postgres_port = 5432
    fake_settings.redis_host = "localhost"
    fake_settings.redis_port = 6379
    fake_settings.trading_mode = "paper"
    fake_settings.kis_app_key = ""
    fake_settings.kis_app_secret = ""
    fake_settings.kis_account_no = ""
    fake_settings.kis_acnt_prdt_cd = "01"
    fake_settings.anthropic_api_key = ""
    fake_settings.slack_webhook_url = ""
    fake_settings.db_url = "sqlite:///:memory:"
    fake_settings.is_live = False

    mod = types.ModuleType("quant_alpha.common.config")
    mod.settings = fake_settings  # type: ignore[attr-defined]

    class _FakeSettings:
        pass

    mod.Settings = _FakeSettings  # type: ignore[attr-defined]
    return mod


def _make_logger_module() -> types.ModuleType:
    """Return a fake quant_alpha.common.logger module with a stdlib-backed logger."""

    import structlog

    # Configure structlog once with a stdlib-compatible setup so add_logger_name
    # works correctly.  Using stdlib.LoggerFactory makes structlog wrap the
    # stdlib logger, which carries a .name attribute.
    logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    def get_logger(name: str) -> structlog.BoundLogger:
        return structlog.get_logger(name)

    def configure_logging(log_level: str = "WARNING") -> None:  # noqa: ARG001
        pass

    mod = types.ModuleType("quant_alpha.common.logger")
    mod.get_logger = get_logger  # type: ignore[attr-defined]
    mod.configure_logging = configure_logging  # type: ignore[attr-defined]
    return mod


def pytest_configure(config):  # noqa: ARG001
    """Inject safe module stubs before any src import during collection."""
    sys.modules["quant_alpha.common.config"] = _make_settings_module()
    sys.modules["quant_alpha.common.logger"] = _make_logger_module()
