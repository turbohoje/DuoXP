# DuoXP Debugging Findings

## Environment
- Python 3.14.3
- macOS Darwin 25.4.0
- Chrome 147 / ChromeDriver (managed by Selenium)

---

## Issues Found and Fixed

### 1. Python 3.14 incompatibility — `urllib3` / `six`
**File:** `requirements.txt`

`urllib3==1.26.2` vendors `six` internally, and `urllib3.packages.six.moves` is broken on Python 3.14. This caused an immediate `ModuleNotFoundError` on import, preventing the script from running at all.

**Fix:** Upgraded to `selenium>=4.43.0` and `urllib3>=2.0.0`. The new selenium pulls in urllib3 2.x which drops the `six` dependency entirely.

---

### 2. Missing import — `UnexpectedAlertPresentException`
**File:** `duolingo_scraper.py`, line 5

`UnexpectedAlertPresentException` was used in two `except` clauses but never imported, which would have caused a `NameError` at runtime.

**Fix:** Added to the selenium exceptions import line.

---

### 3. Duplicate `except` block
**File:** `duolingo_scraper.py`

Two identical `except UnexpectedAlertPresentException` clauses existed back-to-back. The second was dead code.

**Fix:** Replaced the second with `except NoSuchWindowException` (see below).

---

### 4. `NoSuchWindowException` not caught
**File:** `duolingo_scraper.py`

If the Chrome window was closed while the script was running, `NoSuchWindowException` would propagate uncaught and crash the process. This happened both inside `autoXP()` and in the top-level `while True` loop.

**Fix:** Added `NoSuchWindowException` to the `except` block inside `autoXP`, and wrapped the main loop's `Duo.autoXP()` call in a `try/except NoSuchWindowException` that breaks cleanly.

---

### 5. Invalid regex escape sequences
**File:** `duolingo_scraper.py`, lines 213 and 216

```python
re.sub('^\d\\n', '', i.text)  # SyntaxWarning in Python 3.12+, will error in future
```

**Fix:** Changed to raw strings: `re.sub(r'^\d\n', '', i.text)`

---

### 6. `loginDuo` had a hardcoded bypass
**File:** `duolingo_scraper.py`

The login function had `if True: return` after a 20-second manual countdown, completely skipping credential entry. The actual login automation code was present but unreachable.

**Fix:** Removed the countdown and bypass. Rewrote `loginDuo` to:
- Use `WebDriverWait` / `EC.element_to_be_clickable` instead of fixed sleeps
- Find the "I already have an account" button by text content (case-insensitive translate XPath)
- Detect login success by checking whether the URL still contains `isLoggingIn`
- Retry up to 3 times, re-entering credentials on each attempt

---

### 7. React form not accepting `send_keys` / `element.clear()`
**File:** `duolingo_scraper.py`, `loginDuo`

Duolingo's login form is a React app. Selenium's `element.clear()` directly mutates the DOM value without firing React's synthetic keyboard events, so React's internal state stays empty and the form submits blank credentials despite the field appearing filled.

**Fix:** Replaced `clear()` + `send_keys(full_string)` with a `type_slowly()` helper that:
1. Clicks the field to focus it
2. Sends `Ctrl+A` to select existing content (also React-safe)
3. Types each character individually with a random 50–150ms delay between keystrokes

This fires a proper sequence of `keydown`/`keypress`/`keyup`/`input` events that React's event system processes correctly, and also mimics human typing to avoid bot detection.

---

## Current Status

Login works end-to-end and redirects to `https://www.duolingo.com/learn`. The `autoXP()` loop runs but exits via `NoSuchElementException` on the first step — the hardcoded XPaths targeting the lesson at `/lesson/unit/37/level/2` appear to be stale (Duolingo's DOM structure has changed). The lesson automation will need the XPaths re-mapped against the current page structure.
