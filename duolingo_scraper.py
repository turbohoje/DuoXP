#!/usr/bin/env python3
# Selenium imports.
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, NoSuchWindowException, StaleElementReferenceException, TimeoutException, UnexpectedAlertPresentException
import base64, json, os, re, sys, time

COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "duo_cookies.json")
MISSES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "word_match_misses.json")


def record_miss(word):
    # Word-pair misses tell us which entries the `phrases` dict is missing or
    # has wrong. Keyed by the word so the file stays a unique set, with a hit
    # count so the common ones stand out.
    try:
        with open(MISSES_FILE) as f:
            misses = json.load(f)
    except (FileNotFoundError, ValueError):
        misses = {}
    misses[word] = misses.get(word, 0) + 1
    with open(MISSES_FILE, "w") as f:
        json.dump(misses, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(f"MISS: {word!r} (seen {misses[word]}x)")

# Other imports.
from keys import username, password
# Class for learning OOP


class Duolingo:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        # Comment the line below to switch OFF incognito mode.
        #chrome_options.add_argument("--incognito")
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--mute-audio")
        # Suppress Chrome's "save password?" bubble — it can steal focus
        # and inject characters into the password field mid-typing.
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "autofill.profile_enabled": False,
        })
        # Hide the standard Selenium/automation fingerprints. Even after manual
        # login, Duolingo continues to score authenticated requests via
        # reCAPTCHA v3, and a clean fingerprint reduces the chance of a
        # session getting silently invalidated mid-scrape.
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        self.driver = webdriver.Chrome(options=chrome_options)
        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
            )
        except Exception as e:
            print(f"could not patch navigator.webdriver: {e}")

    def closeBrowser(self):
        self.driver.close()

    def _save_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
            print(f"saved {len(cookies)} cookies to {COOKIE_FILE}")
        except Exception as e:
            print(f"could not save cookies: {e}")

    def _load_cookies(self):
        # Duolingo's session is carried by a `jwt_token` cookie. We can skip
        # the login form entirely by injecting it. reCAPTCHA v3 only gates
        # the /login endpoint, not authenticated requests, so once we have
        # a valid jwt_token the rest of the scraper works unchanged.
        if not os.path.exists(COOKIE_FILE):
            print("no saved cookies; manual login required")
            return False
        try:
            with open(COOKIE_FILE) as f:
                cookies = json.load(f)
        except Exception as e:
            print(f"could not read cookie file: {e}")
            return False
        # Selenium requires the domain to be loaded before add_cookie.
        self.driver.get("https://www.duolingo.com/")
        for cookie in cookies:
            cookie.pop("sameSite", None)
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"  could not restore cookie {cookie.get('name')!r}: {e}")
        print(f"restored {len(cookies)} cookies from {COOKIE_FILE}")
        return True

    def _is_logged_in(self):
        # /learn redirects unauthenticated users to ?isLoggingIn=true.
        self.driver.get("https://www.duolingo.com/learn")
        time.sleep(2)
        url = self.driver.current_url
        return "/learn" in url and "isLoggingIn" not in url

    def loginDuo(self, username, password):
        print("logging in")
        driver = self.driver

        # 1) Try cookie reuse first.
        if self._load_cookies():
            if self._is_logged_in():
                print("logged in via saved cookies")
                return
            print("saved cookies are stale; falling back to manual login")

        # 2) Manual login fallback. Duolingo's /2023-05-23/login endpoint is
        #    gated by reCAPTCHA v3, which silently scores the request and
        #    rejects automated submissions with a misleading 401 "wrong
        #    password" response. The score depends on real human signals
        #    (mouse movement, browsing history, fingerprint), so we let the
        #    human do the actual submit and then capture the resulting
        #    session cookies for future runs.
        driver.get("https://www.duolingo.com/?isLoggingIn=true")
        banner = (
            "\n" + "=" * 72 + "\n"
            "  MANUAL LOGIN REQUIRED\n"
            f"  Username: {username}\n"
            f"  Password is in keys.py — copy-paste it into the Chrome window.\n"
            "  Waiting up to 5 minutes for you to finish logging in...\n"
            + "=" * 72 + "\n"
        )
        print(banner)

        deadline = time.time() + 300
        last_url = ""
        while time.time() < deadline:
            try:
                cur = driver.current_url
            except NoSuchWindowException:
                raise
            if cur != last_url:
                print(f"  url: {cur}")
                last_url = cur
            # We're logged in once the URL leaves the login flow and lands on
            # an authenticated page like /learn or /lesson.
            if ("/learn" in cur or "/lesson" in cur) and "isLoggingIn" not in cur:
                print("manual login detected")
                break
            time.sleep(2)
        else:
            raise TimeoutException("manual login window expired")

        self._save_cookies()
        time.sleep(1)

    def _decode_jwt_sub(self):
        # Duolingo's session cookie is a standard JWT; the user id lives in the
        # `sub` claim of the middle (payload) segment.
        cookie = self.driver.get_cookie("jwt_token")
        if not cookie:
            raise RuntimeError("no jwt_token cookie; cannot determine user id")
        payload_b64 = cookie["value"].split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        sub = payload.get("sub")
        if not sub:
            raise RuntimeError(f"jwt_token has no `sub` claim: {list(payload)}")
        return sub

    def _ensure_spanish_course(self):
        # The active course lives on the user object server-side, not in a
        # cookie. Read it via the same endpoint the web app uses, and PATCH
        # back to Spanish if the account has been switched to another course.
        driver = self.driver
        # fetch() needs to run on the duolingo.com origin so cookies are sent.
        if "duolingo.com" not in (driver.current_url or ""):
            driver.get("https://www.duolingo.com/learn")
            time.sleep(1)

        sub = self._decode_jwt_sub()
        base_path = f"/2017-06-30/users/{sub}"

        get_script = """
            const path = arguments[0];
            const done = arguments[arguments.length - 1];
            fetch(path, {credentials: 'include'})
                .then(r => r.text().then(t => ({status: r.status, body: t})))
                .then(done)
                .catch(e => done({error: String(e)}));
        """
        resp = driver.execute_async_script(
            get_script, base_path + "?fields=learningLanguage,fromLanguage"
        )
        if resp.get("error") or resp.get("status") != 200:
            raise RuntimeError(f"could not read user course: {resp}")
        data = json.loads(resp["body"])
        current = data.get("learningLanguage")
        from_lang = data.get("fromLanguage") or "en"
        if current == "es":
            print(f"course already set to Spanish (from {from_lang})")
            return

        print(f"current course is {current!r}; switching to Spanish")
        patch_script = """
            const path = arguments[0];
            const body = arguments[1];
            const done = arguments[arguments.length - 1];
            fetch(path, {
                method: 'PATCH',
                credentials: 'include',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body),
            })
            .then(r => r.text().then(t => ({status: r.status, body: t})))
            .then(done)
            .catch(e => done({error: String(e)}));
        """
        result = driver.execute_async_script(
            patch_script, base_path, {"fromLanguage": from_lang, "learningLanguage": "es"}
        )
        if result.get("error") or result.get("status") not in (200, 201, 204):
            raise RuntimeError(f"could not switch course to Spanish: {result}")

        # Verify the switch actually took.
        verify = driver.execute_async_script(
            get_script, base_path + "?fields=learningLanguage"
        )
        if verify.get("status") != 200 or json.loads(verify["body"]).get("learningLanguage") != "es":
            raise RuntimeError(f"course switch did not take: {verify}")
        print("course switched to Spanish")

    def autoXP(self):
        driver = self.driver

        self._ensure_spanish_course()
        driver.get("https://www.duolingo.com/lesson/unit/37/level/2")
        time.sleep(4)
        try:
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div/div[3]/button').click()
            time.sleep(2)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(2)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(2)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(3)
            print("novio button")
            # Duolingo now exposes tap-tokens via stable data-test slugs of the
            # form "<word>-challenge-tap-token". The old absolute XPath broke
            # when they restructured the surrounding DOM.
            driver.find_element("css selector", '[data-test="novio-challenge-tap-token"]').click()
            time.sleep(1)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
            time.sleep(4)
            #phrase
            a = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[11]/div/ul/li[1]/button')
            b = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[11]/div/ul/li[2]/button')
            c = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[11]/div/ul/li[3]/button')


            if a.text == "Estoy muy emocionada":
                a.click()
            elif b.text == "Estoy muy emocionada":
                b.click()
            elif c.text == "Estoy muy emocionada":
                c.click()

            for i in range(1, 7):
                print(i)
                driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
                time.sleep(5)

            print("propose choice")
            # #propose coice
            a = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[17]/div/ul/li[1]')
            b = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[17]/div/ul/li[2]')
            c = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[17]/div/ul/li[3]')

            print(a.text)
            print(b.text)
            print(c.text)

            if a.text == "…propose to her boyfriend this weekend.":
                a.click()
            elif b.text == "…propose to her boyfriend this weekend.":
                b.click()
            elif c.text == "…propose to her boyfriend this weekend.":
                c.click()

            for i in range(1, 7):
                print(i)
                driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
                time.sleep(4)

            a = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[25]/div/ul/li[1]/button')
            b = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[25]/div/ul/li[2]/button')
            c = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[25]/div/ul/li[3]/button')

            if a.text == "Ya conoces a":
                a.click()
            elif b.text == "Ya conoces a":
                b.click()
            elif c.text == "Ya conoces a":
                c.click()

            for i in range(1, 6):
                print(i)
                driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()
                time.sleep(4)

            a = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[30]/div/ul/li[1]')
            b = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[30]/div/ul/li[2]')
            c = driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[30]/div/ul/li[3]')

            print(a.text)
            print(b.text)
            print(c.text)

            if a.text == "…that his girlfriend is going to propose to him.":
                a.click()
            elif b.text == "…that his girlfriend is going to propose to him.":
                b.click()
            elif c.text == "…that his girlfriend is going to propose to him.":
                c.click()
            else:
                print("no match")

            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div/div/button').click()

            l = []
            r = []
            #end buttons                           /html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[1]/li[1]/span/button
            l.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[1]/li[1]/span/button'))
            l.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[1]/li[2]/span/button'))
            l.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[1]/li[3]/span/button'))
            l.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[1]/li[4]/span/button'))
            l.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[1]/li[5]/span/button'))

            r.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[2]/li[1]/span/button'))
            r.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[2]/li[2]/span/button'))
            r.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[2]/li[3]/span/button'))
            r.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[2]/li[4]/span/button'))
            r.append(driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[31]/div/div[2]/div/ul[2]/li[5]/span/button'))

            phrases = {
                "with" : "con",
                "so" : "tan",
                "really" : "de verdad",
                "boyfriend" : "novio",
                "to meet" : "conocer",
                "I am waiting for": "estoy esperando",
                "interesting": "interesante",
                "nice to meet you" : "mucho gusto",
                "friend" : "amiga",
                "she's going to come" : "va a venir",
                "already":"ya",
                "to propose":"pedir matrimonio",
                "park":"parque",
                "weekend":"fin de semana",
                "romantic":"romántico"
            }

            for i in l:
                ik = re.sub(r'^\d\n', '', i.text)
                print("examining " + ik)
                want = phrases.get(ik)
                if want is None:
                    # Not in the dict at all — previously this raised KeyError
                    # and abandoned the rest of the lesson.
                    record_miss(ik)
                    continue
                for j in r:
                    jk = re.sub(r'^\d\n', '', j.text)
                    print("comparing " + jk)
                    if jk == want:
                        i.click()
                        j.click()
                        print("match")
                        time.sleep(1)
                        break
                else:
                    # Known word, but its translation wasn't on screen.
                    record_miss(ik)

            time.sleep(8)
            print("done1")
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div[2]/div/button').click()
            time.sleep(8)
            print("done2")
            # Post-lesson summary screens (XP earned, league progress, etc.)
            # vary in number — sometimes the lesson redirects straight to /learn
            # with no extra screens. Swallow NSE on these trailing clicks so a
            # successful lesson completion doesn't surface as an error.
            try:
                driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[2]/div/div/div/button').click()
                time.sleep(8)
                print("done3")
                for i in range(1, 3):
                    driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[2]/div/div/div/button').click()
                    time.sleep(8)
                    print("final %i", i)
            except NoSuchElementException:
                print("lesson complete (no further summary screens)")
        # Debugging code.

        # except:
        #     pass
        except ElementClickInterceptedException:
            print("Done CIE")
        except NoSuchElementException:
            print("Ok nse returning")
            driver.get("https://www.duolingo.com/learn") #go back and be ready
            driver.execute_script("window.onbeforeunload = function() {};")
        except StaleElementReferenceException:
            print("Ok stale")
        except KeyError:
            print("Key error")
        except UnexpectedAlertPresentException:
            print("do nothing")
        except NoSuchWindowException:
            print("window closed, exiting")
        
        print("done")


Duo = Duolingo()
Duo.loginDuo(username, password)

def read_timeout(filename):
    try:
        with open(filename, 'r') as file:
            timeout = file.readline().strip()
            return int(timeout)  # Convert to integer
    except FileNotFoundError:
        print("Error: File not found.")
        return None
    except ValueError:
        print("Error: Invalid timeout value.")
        return None
    
def countdown(seconds):
    for remaining in range(seconds, 0, -1):
        sys.stdout.write(f"\rTime remaining: {remaining} seconds ")
        sys.stdout.flush()
        time.sleep(1)


while True:
    try:
        Duo.autoXP()
    except NoSuchWindowException:
        print("window closed, stopping")
        break
    print("sleeping")
    timeout_value = read_timeout("timeout.txt")
    countdown(timeout_value)
