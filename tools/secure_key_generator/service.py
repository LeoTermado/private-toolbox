"""Secure Key Generator — generation, validation, entropy and formatting logic.

No Flask, no file I/O. Generated secrets exist only as return values for the
current request; nothing here writes, prints, logs or persists a generated value.

Security notes:
  * All randomness comes from the ``secrets`` module. ``random`` is never used.
  * Secrets are never saved to disk, never logged, never put into filenames.
  * The only place a generated value goes is the function's return value, which
    the route renders into the response.
"""
import base64
import json
import math
import re
import secrets

from .wordlist import WORDS, WORDLIST_SIZE

# --- Character groups ---------------------------------------------------------
UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
NUMBERS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{}:,.?"

# Visually ambiguous look-alikes, removed when "exclude ambiguous" is on.
AMBIGUOUS = set("0Oo1lI|")

# Characters that tend to break shells, connection strings and config files.
# Removed when "exclude shell-unfriendly" is on (and forced on for DB passwords).
SHELL_UNFRIENDLY = set("\"'`\\ /;|&$<>(){}[]*?!~^#%=:,@")

# Recovery codes use an unambiguous uppercase+digit alphabet by default.
RECOVERY_ALPHABET = "".join(c for c in (UPPERCASE + NUMBERS) if c not in AMBIGUOUS)

MODES = {
    "password", "hex_key", "base64_key", "urlsafe_token",
    "numeric", "recovery_codes", "passphrase",
}
OUTPUT_TEMPLATES = {"plain", "plain_list", "env", "json", "yaml", "java", "python"}
PP_SEPARATORS = {"hyphen": "-", "underscore": "_", "dot": ".", "space": " "}
PP_CAPITALIZE = {"none", "title", "upper"}
CODE_SEPARATORS = {"-", "_", "."}

# --- Limits (also enforced client-side, but the server is the source of truth) -
LIMITS = {
    "count_min": 1, "count_max": 100,
    "password_len_min": 4, "password_len_max": 512,
    "byte_len_min": 4, "byte_len_max": 256,
    "numeric_len_min": 4, "numeric_len_max": 64,
    "rc_len_min": 8, "rc_len_max": 64,
    "rc_group_min": 2, "rc_group_max": 12,
    "word_min": 3, "word_max": 12,
    "prefix_max": 32,
    "varname_max": 64,
    "custom_symbols_max": 64,
}

_VARNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PREFIX_RE = re.compile(r"^[A-Za-z0-9_.\-]*$")

# --- Defaults for every form field -------------------------------------------
DEFAULTS = {
    "preset": "login_password",
    "mode": "password",
    "count": 1,
    # password
    "length": 20,
    "uppercase": True,
    "lowercase": True,
    "numbers": True,
    "symbols": True,
    "exclude_ambiguous": True,
    "exclude_shell_unfriendly": False,
    "custom_symbols": "",
    "min_upper": 0,
    "min_lower": 0,
    "min_number": 0,
    "min_symbol": 0,
    "allow_repeats": True,
    "allow_spaces": False,
    # token / key
    "byte_length": 32,
    "prefix": "",
    "base64_urlsafe": True,
    # numeric
    "numeric_length": 6,
    # recovery codes
    "rc_length": 12,
    "rc_group_size": 4,
    "rc_separator": "-",
    # passphrase
    "word_count": 4,
    "pp_separator": "hyphen",
    "pp_add_number": False,
    "pp_capitalize": "none",
    # output
    "output_template": "plain",
    "variable_name": "",
    # Privacy-first: secrets are hidden by default and only revealed by user action.
    "hide_result": True,
}


# --- Presets ------------------------------------------------------------------
# Each preset is a *shortcut*: it only overrides the relevant fields. Security
# comes from `secrets` + entropy, never from the preset itself. Presets are fully
# editable on the client; editing flips the selection to "other".
PRESETS = {
    "login_password": {
        "label": "Login password",
        "help": "Normal website or app login password.",
        "settings": {
            "mode": "password", "length": 20, "count": 1,
            "uppercase": True, "lowercase": True, "numbers": True, "symbols": True,
            "exclude_ambiguous": True, "exclude_shell_unfriendly": False,
            "output_template": "plain", "hide_result": True,
        },
    },
    "admin_password": {
        "label": "Admin password",
        "help": "Privileged accounts: admin panels, dashboards, infrastructure tools.",
        "settings": {
            "mode": "password", "length": 32, "count": 1,
            "uppercase": True, "lowercase": True, "numbers": True, "symbols": True,
            "exclude_ambiguous": True, "exclude_shell_unfriendly": False,
            "output_template": "plain", "hide_result": True,
        },
    },
    "database_password": {
        "label": "Database password",
        "help": "Safe to paste into .env files, connection strings and config files "
                "(shell-unfriendly characters are excluded).",
        "settings": {
            "mode": "password", "length": 40, "count": 1,
            "uppercase": True, "lowercase": True, "numbers": True, "symbols": True,
            "exclude_ambiguous": True, "exclude_shell_unfriendly": True,
            "output_template": "env", "variable_name": "DATABASE_PASSWORD",
        },
    },
    "api_token": {
        "label": "API token",
        "help": "URL-safe token for local tools, APIs, headers and scripts. "
                "Add an optional prefix like dev_sk_.",
        "settings": {
            "mode": "urlsafe_token", "byte_length": 32, "count": 1,
            "prefix": "", "output_template": "plain",
        },
    },
    "session_secret": {
        "label": "Session secret",
        "help": "Secret key for signing sessions in web frameworks.",
        "settings": {
            "mode": "urlsafe_token", "byte_length": 48, "count": 1,
            "prefix": "", "output_template": "env", "variable_name": "SESSION_SECRET",
        },
    },
    "framework_secret": {
        "label": "Flask / Django secret key",
        "help": "Framework secret key for local Flask or Django apps.",
        "settings": {
            "mode": "urlsafe_token", "byte_length": 50, "count": 1,
            "prefix": "", "output_template": "env", "variable_name": "SECRET_KEY",
        },
    },
    "jwt_secret": {
        "label": "JWT / HMAC secret",
        "help": "Secret for signing JWTs or HMAC values (64 bytes, Base64).",
        "settings": {
            "mode": "base64_key", "byte_length": 64, "count": 1,
            "prefix": "", "base64_urlsafe": True,
            "output_template": "env", "variable_name": "JWT_SECRET",
        },
    },
    "enc_128": {
        "label": "Encryption key 128-bit",
        "help": "16 bytes = 128 bits. For tools that require exactly 128 bits.",
        "settings": {
            "mode": "hex_key", "byte_length": 16, "count": 1,
            "prefix": "", "output_template": "plain",
        },
    },
    "enc_256": {
        "label": "Encryption key 256-bit",
        "help": "32 bytes = 256 bits. For tools that require exactly 256 bits.",
        "settings": {
            "mode": "hex_key", "byte_length": 32, "count": 1,
            "prefix": "", "output_template": "plain",
        },
    },
    "numeric_pin": {
        "label": "Numeric PIN",
        "help": "Temporary numeric codes only. PINs have low entropy — do not use "
                "them as long-term secrets.",
        "settings": {
            "mode": "numeric", "numeric_length": 6, "count": 5,
            "output_template": "plain",
        },
    },
    "recovery_codes": {
        "label": "Recovery codes",
        "help": "Multiple grouped backup codes (e.g. ABCD-EFGH-JKLM).",
        "settings": {
            "mode": "recovery_codes", "count": 10, "rc_length": 12,
            "rc_group_size": 4, "rc_separator": "-", "output_template": "plain_list",
        },
    },
    "passphrase": {
        "label": "Memorable passphrase",
        "help": "Random words from a local bundled list. Easy to remember, still "
                "generated with secrets.",
        "settings": {
            "mode": "passphrase", "word_count": 4, "pp_separator": "hyphen",
            "count": 1, "pp_add_number": True, "pp_capitalize": "none",
            "output_template": "plain",
        },
    },
}


class ValidationError(Exception):
    """Raised with a friendly, user-facing message when input is invalid."""


# --- Secure helpers -----------------------------------------------------------
def _secure_shuffle(seq):
    """In-place Fisher-Yates shuffle using secrets (no `random`)."""
    for i in range(len(seq) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        seq[i], seq[j] = seq[j], seq[i]


def _build_password_pool(opts):
    """Return (combined_pool_str, {group_name: chars_str}) after exclusions.

    Only selected, non-empty groups are returned. `symbols` is replaced by the
    user's custom symbol set when provided.
    """
    excluded = set()
    if opts["exclude_ambiguous"]:
        excluded |= AMBIGUOUS
    if opts["exclude_shell_unfriendly"]:
        excluded |= SHELL_UNFRIENDLY

    groups = {}
    if opts["uppercase"]:
        groups["uppercase"] = UPPERCASE
    if opts["lowercase"]:
        groups["lowercase"] = LOWERCASE
    if opts["numbers"]:
        groups["numbers"] = NUMBERS
    if opts["symbols"]:
        symbol_source = opts["custom_symbols"] or SYMBOLS
        groups["symbols"] = symbol_source

    # Spaces are an opt-in extra "group" with no minimum.
    extra = " " if opts["allow_spaces"] else ""

    filtered = {}
    for name, chars in groups.items():
        kept = "".join(dict.fromkeys(c for c in chars if c not in excluded))
        if kept:
            filtered[name] = kept

    combined_chars = "".join(filtered.values()) + extra
    combined = "".join(dict.fromkeys(combined_chars))
    return combined, filtered


# --- Generators ---------------------------------------------------------------
def generate_password(opts):
    pool, groups = _build_password_pool(opts)
    length = opts["length"]
    allow_repeats = opts["allow_repeats"]

    min_map = {
        "uppercase": opts["min_upper"],
        "lowercase": opts["min_lower"],
        "numbers": opts["min_number"],
        "symbols": opts["min_symbol"],
    }

    # Required count per selected group: the user's explicit minimum, bumped to at
    # least 1 when the length leaves room for one of every selected group.
    required = {name: max(0, min_map.get(name, 0)) for name in groups}
    if length >= len(groups):
        for name in groups:
            required[name] = max(required[name], 1)

    used = set()
    chars = []

    def pick(from_chars):
        if allow_repeats:
            return secrets.choice(from_chars)
        avail = [c for c in from_chars if c not in used]
        # Feasibility is guaranteed by validate_options; guard anyway.
        if not avail:
            raise ValidationError(
                "Not enough unique characters for the chosen length without "
                "repeats. Enable repeated characters or shorten the length.")
        c = secrets.choice(avail)
        used.add(c)
        return c

    for name, need in required.items():
        for _ in range(need):
            chars.append(pick(groups[name]))

    for _ in range(length - len(chars)):
        chars.append(pick(pool))

    _secure_shuffle(chars)
    return "".join(chars)


def generate_hex_key(opts):
    # token_hex(n) -> 2n hex chars from n random bytes.
    return opts["prefix"] + secrets.token_hex(opts["byte_length"])


def generate_base64_key(opts):
    raw = secrets.token_bytes(opts["byte_length"])
    if opts["base64_urlsafe"]:
        encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    else:
        encoded = base64.b64encode(raw).decode("ascii")
    return opts["prefix"] + encoded  # single line, no breaks


def generate_urlsafe_token(opts):
    return opts["prefix"] + secrets.token_urlsafe(opts["byte_length"])


def generate_numeric_code(opts):
    return "".join(secrets.choice(NUMBERS) for _ in range(opts["numeric_length"]))


def generate_recovery_codes(opts):
    # Returns a single grouped code; the caller loops `count` times.
    n = opts["rc_length"]
    raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(n))
    size = opts["rc_group_size"]
    sep = opts["rc_separator"]
    groups = [raw[i:i + size] for i in range(0, n, size)]
    return sep.join(groups)


def generate_passphrase(opts):
    sep = PP_SEPARATORS[opts["pp_separator"]]
    cap = opts["pp_capitalize"]
    words = [secrets.choice(WORDS) for _ in range(opts["word_count"])]
    if cap == "title":
        words = [w.capitalize() for w in words]
    elif cap == "upper":
        words = [w.upper() for w in words]
    phrase = sep.join(words)
    if opts["pp_add_number"]:
        # A 2-digit random number (10-99) keeps it memorable; counted in entropy.
        phrase = phrase + sep + str(10 + secrets.randbelow(90))
    return phrase


_SINGLE_GENERATORS = {
    "password": generate_password,
    "hex_key": generate_hex_key,
    "base64_key": generate_base64_key,
    "urlsafe_token": generate_urlsafe_token,
    "numeric": generate_numeric_code,
    "recovery_codes": generate_recovery_codes,
    "passphrase": generate_passphrase,
}


def generate(opts):
    """Generate `count` values for the chosen mode. Returns a list of strings."""
    gen = _SINGLE_GENERATORS[opts["mode"]]
    return [gen(opts) for _ in range(opts["count"])]


# --- Entropy ------------------------------------------------------------------
def estimate_entropy(opts):
    """Return {bits, label, charset_size, detail} estimating per-value strength.

    Entropy is an *estimate* of the random part only (prefixes are excluded).
    """
    mode = opts["mode"]
    charset_size = None
    detail = ""

    if mode == "password":
        pool, _ = _build_password_pool(opts)
        charset_size = len(pool)
        bits = opts["length"] * math.log2(charset_size) if charset_size > 1 else 0.0
        detail = f"{opts['length']} chars from a {charset_size}-character set"
    elif mode in ("hex_key", "base64_key", "urlsafe_token"):
        bits = opts["byte_length"] * 8
        detail = f"{opts['byte_length']} random bytes ({opts['byte_length']} × 8 bits)"
    elif mode == "numeric":
        charset_size = 10
        bits = opts["numeric_length"] * math.log2(10)
        detail = f"{opts['numeric_length']} digits"
    elif mode == "recovery_codes":
        charset_size = len(RECOVERY_ALPHABET)
        bits = opts["rc_length"] * math.log2(charset_size)
        detail = f"{opts['rc_length']} chars from a {charset_size}-character set"
    elif mode == "passphrase":
        bits = opts["word_count"] * math.log2(WORDLIST_SIZE)
        detail = f"{opts['word_count']} words from a {WORDLIST_SIZE}-word list"
        if opts["pp_add_number"]:
            bits += math.log2(90)
            detail += " + a random number"
    else:
        bits = 0.0

    return {
        "bits": round(bits, 1),
        "label": _strength_label(bits),
        "charset_size": charset_size,
        "detail": detail,
    }


def _strength_label(bits):
    if bits < 40:
        return "weak"
    if bits < 60:
        return "okay for temporary use"
    if bits < 100:
        return "strong for many user-facing uses"
    if bits < 128:
        return "very strong"
    return "suitable for app secrets"


# --- Masking ------------------------------------------------------------------
# Visual mask only. The real value is never altered or discarded — masking is
# used for the initial (no-JS / pre-paint) render so a secret is never visible
# while the page is in "hidden" mode. The JS swaps in the real value on reveal.
MASK_CHAR = "•"  # bullet •
MASK_CAP = 32         # don't leak exact length for very long secrets


def mask_value(value, cap=MASK_CAP):
    """Return a fixed-bullet mask for `value` (capped so long secrets don't leak length)."""
    return MASK_CHAR * min(len(value), cap)


# --- Output formatting --------------------------------------------------------
def _env_label(name):
    return name or "SECRET"


def _key_label(name):
    # JSON / YAML conventionally use lower_snake_case keys.
    return (name or "secret").lower()


def _env_value(value):
    """Format a value for a .env line.

    Most secrets are bare tokens and need no quoting. But a value containing
    whitespace, '#', or quote characters (e.g. a space-separated passphrase)
    would be misread by common .env parsers, so wrap those in double quotes and
    escape backslashes and double quotes.
    """
    needs_quote = any(c.isspace() for c in value) or any(c in value for c in '#"\'')
    if not needs_quote:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def format_output(values, template, variable_name):
    """Render the list of generated values into the chosen text template.

    Values are escaped correctly per format. Nothing is written to disk.
    """
    multi = len(values) > 1

    if template == "plain":
        return "\n".join(values)

    if template == "plain_list":
        return "\n".join(values)

    if template == "env":
        base = _env_label(variable_name)
        lines = []
        for i, v in enumerate(values, 1):
            key = f"{base}_{i}" if multi else base
            lines.append(f"{key}={_env_value(v)}")
        return "\n".join(lines)

    if template == "json":
        base = _key_label(variable_name)
        obj = {}
        for i, v in enumerate(values, 1):
            key = f"{base}_{i}" if multi else base
            obj[key] = v
        return json.dumps(obj, indent=2, ensure_ascii=False)

    if template == "yaml":
        base = _key_label(variable_name)
        lines = []
        for i, v in enumerate(values, 1):
            key = f"{base}_{i}" if multi else base
            lines.append(f'{key}: "{_yaml_escape(v)}"')
        return "\n".join(lines)

    if template == "java":
        base = _env_label(variable_name)
        lines = []
        for i, v in enumerate(values, 1):
            name = f"{base}_{i}" if multi else base
            lines.append(f'private static final String {name} = "{_code_escape(v)}";')
        return "\n".join(lines)

    if template == "python":
        base = _env_label(variable_name)
        lines = []
        for i, v in enumerate(values, 1):
            name = f"{base}_{i}" if multi else base
            lines.append(f'{name} = "{_code_escape(v)}"')
        return "\n".join(lines)

    return "\n".join(values)


def _code_escape(value):
    # Escape for double-quoted Java/Python string literals.
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _yaml_escape(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_all_formats(values, variable_name):
    """Precompute every output template so the client can copy any of them."""
    return {t: format_output(values, t, variable_name) for t in OUTPUT_TEMPLATES}


# --- Parsing & validation -----------------------------------------------------
def _as_bool(form, key):
    return form.get(key) in ("on", "true", "1", "yes")


def _as_int(form, key, default):
    raw = (form.get(key) or "").strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"“{key.replace('_', ' ')}” must be a whole number.")


def parse_options(form):
    """Build a normalized options dict from raw form data (no validation yet)."""
    opts = dict(DEFAULTS)
    opts["preset"] = (form.get("preset") or DEFAULTS["preset"]).strip()
    opts["mode"] = (form.get("mode") or DEFAULTS["mode"]).strip()
    opts["count"] = _as_int(form, "count", DEFAULTS["count"])

    # password
    opts["length"] = _as_int(form, "length", DEFAULTS["length"])
    opts["uppercase"] = _as_bool(form, "uppercase")
    opts["lowercase"] = _as_bool(form, "lowercase")
    opts["numbers"] = _as_bool(form, "numbers")
    opts["symbols"] = _as_bool(form, "symbols")
    opts["exclude_ambiguous"] = _as_bool(form, "exclude_ambiguous")
    opts["exclude_shell_unfriendly"] = _as_bool(form, "exclude_shell_unfriendly")
    opts["custom_symbols"] = (form.get("custom_symbols") or "").strip()
    opts["min_upper"] = _as_int(form, "min_upper", 0)
    opts["min_lower"] = _as_int(form, "min_lower", 0)
    opts["min_number"] = _as_int(form, "min_number", 0)
    opts["min_symbol"] = _as_int(form, "min_symbol", 0)
    opts["allow_repeats"] = _as_bool(form, "allow_repeats")
    opts["allow_spaces"] = _as_bool(form, "allow_spaces")

    # token / key
    opts["byte_length"] = _as_int(form, "byte_length", DEFAULTS["byte_length"])
    opts["prefix"] = (form.get("prefix") or "").strip()
    opts["base64_urlsafe"] = (form.get("base64_variant") or "urlsafe") == "urlsafe"

    # numeric
    opts["numeric_length"] = _as_int(form, "numeric_length", DEFAULTS["numeric_length"])

    # recovery codes
    opts["rc_length"] = _as_int(form, "rc_length", DEFAULTS["rc_length"])
    opts["rc_group_size"] = _as_int(form, "rc_group_size", DEFAULTS["rc_group_size"])
    opts["rc_separator"] = (form.get("rc_separator") or "-").strip()

    # passphrase
    opts["word_count"] = _as_int(form, "word_count", DEFAULTS["word_count"])
    opts["pp_separator"] = (form.get("pp_separator") or "hyphen").strip()
    opts["pp_add_number"] = _as_bool(form, "pp_add_number")
    opts["pp_capitalize"] = (form.get("pp_capitalize") or "none").strip()

    # output
    opts["output_template"] = (form.get("output_template") or "plain").strip()
    opts["variable_name"] = (form.get("variable_name") or "").strip()
    opts["hide_result"] = _as_bool(form, "hide_result")
    return opts


def _check_range(value, low, high, label):
    if value < low or value > high:
        raise ValidationError(f"{label} must be between {low} and {high}.")


def validate_options(opts):
    """Validate a parsed options dict. Raises ValidationError with a friendly msg."""
    if opts["mode"] not in MODES:
        raise ValidationError("Unsupported generation mode.")
    if opts["preset"] not in PRESETS and opts["preset"] != "other":
        raise ValidationError("Unknown preset.")
    if opts["output_template"] not in OUTPUT_TEMPLATES:
        raise ValidationError("Unsupported output template.")

    _check_range(opts["count"], LIMITS["count_min"], LIMITS["count_max"], "Count")

    # Prefix (token-like modes only, but validate whenever present).
    if len(opts["prefix"]) > LIMITS["prefix_max"]:
        raise ValidationError(f"Prefix must be at most {LIMITS['prefix_max']} characters.")
    if opts["prefix"] and not _PREFIX_RE.match(opts["prefix"]):
        raise ValidationError(
            "Prefix may only contain letters, numbers, '_', '-' and '.'.")

    # Variable name required for templates that need an identifier.
    if opts["output_template"] in ("env", "json", "yaml", "java", "python"):
        name = opts["variable_name"]
        if name:
            if len(name) > LIMITS["varname_max"]:
                raise ValidationError(
                    f"Variable name must be at most {LIMITS['varname_max']} characters.")
            if not _VARNAME_RE.match(name):
                raise ValidationError(
                    "Variable name must start with a letter or underscore and contain "
                    "only letters, numbers and underscores.")

    mode = opts["mode"]
    if mode == "password":
        _validate_password(opts)
    elif mode in ("hex_key", "base64_key", "urlsafe_token"):
        _check_range(opts["byte_length"], LIMITS["byte_len_min"],
                     LIMITS["byte_len_max"], "Byte length")
    elif mode == "numeric":
        _check_range(opts["numeric_length"], LIMITS["numeric_len_min"],
                     LIMITS["numeric_len_max"], "PIN length")
    elif mode == "recovery_codes":
        _check_range(opts["rc_length"], LIMITS["rc_len_min"],
                     LIMITS["rc_len_max"], "Recovery code length")
        _check_range(opts["rc_group_size"], LIMITS["rc_group_min"],
                     LIMITS["rc_group_max"], "Group size")
        if opts["rc_separator"] not in CODE_SEPARATORS:
            raise ValidationError("Recovery code separator must be '-', '_' or '.'.")
    elif mode == "passphrase":
        _check_range(opts["word_count"], LIMITS["word_min"],
                     LIMITS["word_max"], "Word count")
        if opts["pp_separator"] not in PP_SEPARATORS:
            raise ValidationError("Unsupported passphrase separator.")
        if opts["pp_capitalize"] not in PP_CAPITALIZE:
            raise ValidationError("Unsupported capitalization style.")

    return opts


def _validate_password(opts):
    _check_range(opts["length"], LIMITS["password_len_min"],
                 LIMITS["password_len_max"], "Password length")

    if len(opts["custom_symbols"]) > LIMITS["custom_symbols_max"]:
        raise ValidationError(
            f"Custom symbols must be at most {LIMITS['custom_symbols_max']} characters.")

    if not (opts["uppercase"] or opts["lowercase"]
            or opts["numbers"] or opts["symbols"]):
        raise ValidationError("Select at least one character group for passwords.")

    pool, groups = _build_password_pool(opts)
    if not pool:
        raise ValidationError(
            "No characters available — the exclusions removed every character in "
            "the selected groups. Loosen the exclusions or pick other groups.")

    mins = {
        "uppercase": opts["min_upper"],
        "lowercase": opts["min_lower"],
        "numbers": opts["min_number"],
        "symbols": opts["min_symbol"],
    }
    for name, m in mins.items():
        if m < 0:
            raise ValidationError("Minimum character counts cannot be negative.")
        if m > 0 and name not in groups:
            pretty = name.replace("numbers", "number")
            raise ValidationError(
                f"You set a minimum for {pretty} but that group is not enabled "
                "(or its characters were excluded).")

    total_min = sum(mins.values())
    if total_min > opts["length"]:
        raise ValidationError(
            "The minimum character counts add up to more than the password length.")

    if not opts["allow_repeats"]:
        if opts["length"] > len(pool):
            raise ValidationError(
                f"Without repeated characters the length can be at most {len(pool)} "
                "with the current settings. Enable repeats or shorten the length.")
        for name, m in mins.items():
            if m > 0 and m > len(groups[name]):
                raise ValidationError(
                    f"Minimum for {name} ({m}) exceeds the available unique "
                    f"characters in that group ({len(groups[name])}) when repeats "
                    "are disabled.")


def presets_for_client():
    """Compact preset map (label, help, settings) for embedding as JSON in JS."""
    return {key: {"label": p["label"], "help": p["help"], "settings": p["settings"]}
            for key, p in PRESETS.items()}
