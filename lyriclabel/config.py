from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any
import tomllib


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
_SUPPORTED_KEYS = {
    "lastfm_api_key",
    "quiet",
    "concurrency",
    "dry_run",
    "log_file",
}


@dataclass(frozen=True)
class AppConfig:
    lastfm_api_key: str | None = None
    quiet: bool = False
    concurrency: int = 5
    dry_run: bool = False
    log_file: str | None = None


@dataclass(frozen=True)
class ConfigLoadResult:
    path: Path
    exists: bool
    config: AppConfig
    warnings: list[str] = field(default_factory=list)


def resolve_config_path(config_path: str | None = None) -> Path:
    if config_path:
        return Path(config_path).expanduser().resolve()

    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "lyriclabel" / "config.toml"
        return Path.home() / "AppData" / "Roaming" / "lyriclabel" / "config.toml"

    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home).expanduser().resolve() / "lyriclabel" / "config.toml"
    return Path.home() / ".config" / "lyriclabel" / "config.toml"


def parse_env_bool(value: str | None, *, key_name: str) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"Invalid boolean value for {key_name}: '{value}'. "
        "Use one of: 1/0, true/false, yes/no, on/off."
    )


def _parse_toml_bool(value: Any, *, key_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"Invalid type for '{key_name}' in config.toml. Expected boolean.")


def _parse_toml_int(value: Any, *, key_name: str) -> int:
    if isinstance(value, int):
        return value
    raise ValueError(f"Invalid type for '{key_name}' in config.toml. Expected integer.")


def _parse_toml_str(value: Any, *, key_name: str) -> str:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
        raise ValueError(f"Invalid value for '{key_name}' in config.toml. Empty string is not allowed.")
    raise ValueError(f"Invalid type for '{key_name}' in config.toml. Expected string.")


def _extract_settings_table(parsed: dict[str, Any]) -> dict[str, Any]:
    lyriclabel_section = parsed.get("lyriclabel")
    if lyriclabel_section is None:
        return parsed
    if isinstance(lyriclabel_section, dict):
        return lyriclabel_section
    raise ValueError("Invalid config.toml: [lyriclabel] must be a TOML table.")


def _harden_linux_permissions(path: Path) -> str | None:
    if os.name != "posix":
        return None

    mode = path.stat().st_mode & 0o777
    if mode & 0o077 == 0:
        return None

    try:
        path.chmod(0o600)
        return (
            f"Insecure permissions on config file '{path}' were detected "
            "and automatically tightened to 600."
        )
    except OSError:
        return (
            f"Insecure permissions on config file '{path}'. "
            "Restrict access to owner only (chmod 600)."
        )


def load_config(config_path: str | None = None) -> ConfigLoadResult:
    resolved_path = resolve_config_path(config_path)
    if not resolved_path.exists():
        return ConfigLoadResult(path=resolved_path, exists=False, config=AppConfig())

    warnings: list[str] = []
    permission_warning = _harden_linux_permissions(resolved_path)
    if permission_warning:
        warnings.append(permission_warning)

    try:
        raw_text = resolved_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read config file '{resolved_path}': {exc}") from exc

    try:
        parsed = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Malformed TOML in '{resolved_path}': {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid config format in '{resolved_path}'. Expected TOML table.")

    settings = _extract_settings_table(parsed)
    unknown_keys = sorted(key for key in settings.keys() if key not in _SUPPORTED_KEYS)
    if unknown_keys:
        warnings.append(
            "Unknown config keys ignored: " + ", ".join(unknown_keys)
        )

    config = AppConfig()
    if "lastfm_api_key" in settings:
        config = AppConfig(
            lastfm_api_key=_parse_toml_str(settings["lastfm_api_key"], key_name="lastfm_api_key"),
            quiet=config.quiet,
            concurrency=config.concurrency,
            dry_run=config.dry_run,
            log_file=config.log_file,
        )
    if "quiet" in settings:
        config = AppConfig(
            lastfm_api_key=config.lastfm_api_key,
            quiet=_parse_toml_bool(settings["quiet"], key_name="quiet"),
            concurrency=config.concurrency,
            dry_run=config.dry_run,
            log_file=config.log_file,
        )
    if "concurrency" in settings:
        concurrency = _parse_toml_int(settings["concurrency"], key_name="concurrency")
        if concurrency < 1:
            raise ValueError("Invalid 'concurrency' in config.toml. Must be >= 1.")
        config = AppConfig(
            lastfm_api_key=config.lastfm_api_key,
            quiet=config.quiet,
            concurrency=concurrency,
            dry_run=config.dry_run,
            log_file=config.log_file,
        )
    if "dry_run" in settings:
        config = AppConfig(
            lastfm_api_key=config.lastfm_api_key,
            quiet=config.quiet,
            concurrency=config.concurrency,
            dry_run=_parse_toml_bool(settings["dry_run"], key_name="dry_run"),
            log_file=config.log_file,
        )
    if "log_file" in settings:
        config = AppConfig(
            lastfm_api_key=config.lastfm_api_key,
            quiet=config.quiet,
            concurrency=config.concurrency,
            dry_run=config.dry_run,
            log_file=_parse_toml_str(settings["log_file"], key_name="log_file"),
        )

    return ConfigLoadResult(
        path=resolved_path,
        exists=True,
        config=config,
        warnings=warnings,
    )
