# Gemini TLS Audit

**Date:** 2026-06-20  
**Symptom:** All Gemini calls fail with  
`SSL: CERTIFICATE_VERIFY_FAILED — Basic Constraints of CA cert not marked critical`  
**Affected code:** `code/providers/gemini/_client.py`  
**Environment observed:** Windows 10, Python 3.13.13, OpenSSL 3.0.19

---

## Executive Summary

| Item | Finding |
| --- | --- |
| **Root cause** | Python 3.13 enables `ssl.VERIFY_X509_STRICT` by default. The server certificate chain presented by `generativelanguage.googleapis.com` includes an intermediate CA whose **Basic Constraints** extension is not marked **critical**, which strict RFC 5280 validation rejects. |
| **Client defect** | `GeminiClient` calls `urllib.request.urlopen()` **without an explicit `SSLContext`**, inheriting the Python 3.13 default strict flags. |
| **Not the root cause** | Missing `certifi`, missing Windows trust store, wrong API key, or orchestration/rules logic. |
| **Minimal fix** | Pass a default TLS context with `VERIFY_X509_STRICT` cleared into `urlopen()` inside `_client.py` only. |

---

## 1. HTTP Client Implementation

### Current implementation

```92:99:code/providers/gemini/_client.py
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Gemini HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc
```

| Property | Value |
| --- | --- |
| Library | Stdlib `urllib.request` (no `requests`, `httpx`, or `google-genai`) |
| TLS handling | Implicit — no `context=` argument |
| Retries / timeout | `retry_with_backoff` + `timeout=` on `urlopen` |
| Certificate pinning | None |
| Custom CA path | None |
| Proxy support | None |

When `context` is omitted, CPython 3.13 builds a default context via `ssl.create_default_context()`, which sets:

- `verify_mode = CERT_REQUIRED`
- `check_hostname = True`
- **`verify_flags |= VERIFY_X509_PARTIAL_CHAIN | VERIFY_X509_STRICT`** (new in 3.13)

The failure occurs **during the TLS handshake**, before HTTP status is returned. The pipeline correctly maps this to `ProviderError` → fail-safe NEI.

### Reproduction on this machine

```text
# Default context (same as GeminiClient)
urllib.request.urlopen("https://generativelanguage.googleapis.com")
→ URLError: Basic Constraints of CA cert not marked critical

# Relaxed strict flag only (TLS succeeds; HTTP 404 on bare URL — expected)
ctx = ssl.create_default_context()
ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
urllib.request.urlopen(url, context=ctx)
→ HTTPError 404 (TLS OK)
```

---

## 2. Certificate Bundle Usage

| Mechanism | Used by GeminiClient? | Notes |
| --- | --- | --- |
| **`certifi` bundle** | No | Not imported or referenced anywhere under `code/providers/` |
| **`SSL_CERT_FILE` / `SSL_CERT_DIR`** | Only if set in environment | Not set by this project |
| **`ssl.create_default_context()`** | Yes (implicit via `urlopen`) | On Windows, calls `SSLContext.load_default_certs()` → Windows ROOT store |
| **Explicit `cafile=` / `capath=`** | No | |

### certifi experiment (diagnostic)

```python
ctx = ssl.create_default_context(cafile=certifi.where())
urllib.request.urlopen("https://generativelanguage.googleapis.com", context=ctx)
```

Result: **different** error — `unable to get local issuer certificate` — not a fix. The Mozilla bundle alone does not include the full chain Google presents for this hostname, and it does not address `VERIFY_X509_STRICT`.

**Conclusion:** Adding `certifi` as a dependency without changing verify flags would **not** resolve this failure.

---

## 3. Windows Certificate Store Usage

On Windows, `ssl.create_default_context()` loads trusted roots from the system store via `load_default_certs(Purpose.SERVER_AUTH)`.

| Host | Default Python 3.13 context |
| --- | --- |
| `https://www.google.com` | **TLS OK** |
| `https://generativelanguage.googleapis.com` | **FAIL** (Basic Constraints / strict) |
| `https://pypi.org` | **FAIL** (same strict error) |

This proves:

1. The Windows trust store **is** reachable and working (google.com succeeds).
2. The failure is **hostname/chain-specific strict validation**, not an empty or broken Windows CA store.
3. Browser / Edge can still trust the host while Python 3.13 stdlib rejects it under `VERIFY_X509_STRICT`.

`ssl.enum_certificates('CA')` is available on this platform but is **not** used by the current client.

---

## 4. `requests` / `certifi` Configuration

| Item | Status |
| --- | --- |
| `requests` in project dependencies | **No** (`pyproject.toml` lists only `pydantic`, `python-dotenv`) |
| `certifi` in project dependencies | **No** |
| `requests` installed in user env | Yes (2.33.1) — still **fails** against `generativelanguage.googleapis.com` with the same class of SSL error |
| urllib3 strict flags (2.4+) | Aligns with Python 3.13 defaults when using `requests` without a custom adapter |

**Conclusion:** Switching to `requests` + `certifi` alone is **not** a minimal fix and would introduce a new dependency without guaranteed relief. The issue is the **strict verify flag**, not HTTP library choice.

---

## Root Cause (Detailed)

```text
Python 3.13 ssl.create_default_context()
    → VERIFY_X509_STRICT enabled
        → OpenSSL rejects intermediate CA in Google's chain
            → Basic Constraints extension present but NOT marked critical
                → SSLCertVerificationError before HTTP request
                    → GeminiClient wraps as ProviderError
                        → orchestration fail-safe → not_enough_information
```

This is a **known Python 3.13 breaking change** ([CPython ssl docs](https://docs.python.org/3/library/ssl.html), [urllib3 #3571](https://github.com/urllib3/urllib3/issues/3571)). It affects any endpoint whose chain includes legacy/non-RFC-5280-perfect intermediates—not a misconfiguration of `GOOGLE_API_KEY`.

**Security note:** API key validity was not tested here because TLS fails before authentication matters. **Do not commit API keys**; rotate any key pasted into chat or logs.

---

## Minimal Fix

**Scope:** `code/providers/gemini/_client.py` only — no changes to rules, orchestration, or business logic.

### Recommended (provider transport layer)

Create a module-level SSL context once and pass it to `urlopen`:

```python
import ssl
from urllib import request

def _gemini_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # Python 3.13+ strict RFC 5280 checks reject some public Google chains.
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx

_GEMINI_SSL_CONTEXT = _gemini_ssl_context()

# In _post_generate_content:
with request.urlopen(req, timeout=self.timeout_seconds, context=_GEMINI_SSL_CONTEXT) as response:
    ...
```

| Property | Value |
| --- | --- |
| Hostname verification | **Still enabled** (`check_hostname=True`) |
| CA verification | **Still enabled** (`CERT_REQUIRED`) |
| Relaxed check | Only `VERIFY_X509_STRICT` (Basic Constraints criticality) |
| Risk | Slightly looser than Python 3.13 default; same effective behavior as Python ≤3.12 |

### Alternatives (not minimal)

| Option | Trade-off |
| --- | --- |
| Pin runtime to **Python 3.12** | Avoids code change; judge env may still use 3.13 |
| **`pip install google-genai`** official SDK | Larger dependency; may bundle its own HTTP/TLS stack |
| **`SSL_CERT_FILE` + custom bundle** | Does not remove strict flag; insufficient alone |
| **`verify=False`** | **Unacceptable** — disables all certificate verification |
| Corporate proxy custom CA | Only needed if MITM proxy present; not indicated here |

### Verification after fix

```bash
cd code
python -c "from dotenv import load_dotenv; load_dotenv(); from providers.gemini._client import GeminiClient; c=GeminiClient(); print(c.generate_json(model='gemini-2.5-flash', system_instruction='json', user_text='{\"ok\":true}')[:50])"
python main.py          # regenerate output.csv
python -m evaluation.main
```

Expect non-NEI rows when vision + rules align; TLS errors should disappear from `decision_traces` `PROVIDER-FAILURE` entries.

---

## Impact on Submission Artifacts

| Artifact | Current state (pre-fix) |
| --- | --- |
| `output.csv` | 44/44 `not_enough_information` with Gemini SSL errors in justifications |
| `decision_traces/` | `PROVIDER-FAILURE` rule hits on every claim |
| `evaluation_report.md` | ~15% accuracy; model predicts NEI for all sample rows |

Fixing TLS in `_client.py` unblocks the provider layer; prediction quality still depends on prompts and rules.

---

## Audit Checklist

| # | Question | Answer |
| --- | --- | --- |
| 1 | Does the client use explicit TLS configuration? | **No** — root defect |
| 2 | Is certifi required? | **No** — not used; would not fix strict flag |
| 3 | Is Windows cert store loaded? | **Yes** (implicit) — not the failure mode |
| 4 | Is this an API key problem? | **No** — TLS fails before HTTP auth |
| 5 | Is mock fallback working? | **Yes** — when key absent or after ProviderError |
| 6 | Minimal code change? | **`_client.py` SSL context only** |

---

## References

- [Python 3.13 whatsnew — ssl strict verification](https://docs.python.org/3/whatsnew/3.13.html)
- [ssl.VERIFY_X509_STRICT documentation](https://docs.python.org/3/library/ssl.html#ssl.VERIFY_X509_STRICT)
- [urllib3 issue #3571 — VERIFY_X509_STRICT parity](https://github.com/urllib3/urllib3/issues/3571)
- [Stack Overflow — Basic Constraints / Python 3.13 requests](https://stackoverflow.com/questions/79936555)
