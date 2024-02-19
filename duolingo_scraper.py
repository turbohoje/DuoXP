#!/usr/bin/env python
# Selenium imports.
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
import re

# Other imports.
import time
from keys import username, password
# Class for learning OOP


class Duolingo:
    def __init__(self):
        self.driver = webdriver.Chrome()# Selenium imports.
        chrome_options = webdriver.ChromeOptions()

        # Comment the line below to switch OFF incognito mode.
        chrome_options.add_argument("--incognito")
        # Uncomment the line below to not open a browser window.
        # chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def closeBrowser(self):
        self.driver.close()

    def loginDuo(self, username, password):
        driver = self.driver
        driver.get("https://www.duolingo.com/?isLoggingIn=true")
        time.sleep(2)

        # Hardcoded XPaths.
        driver.find_element("xpath", 
            '//*[@id="root"]/div[1]/header/div[2]/div[2]/div/button').click()
        time.sleep(1)

        # Insertinf credentials.
        driver.find_element("xpath", 
            '/html/body/div[2]/div[3]/div/div/form/div[1]/div[1]/div[1]/div[1]/input').send_keys(username)
        driver.find_element("xpath", 
            '/html/body/div[2]/div[3]/div/div/form/div[1]/div[1]/div[2]/div[1]/input').send_keys(password)
        driver.find_element("xpath", '/html/body/div[2]/div[3]/div/div/form/div[1]/button').click()
        time.sleep(18)

    def autoXP(self):
        driver = self.driver

        driver.get("https://www.duolingo.com/lesson/unit/22/level/7")
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
            #novio button                 /html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[7]/div/div[2]/div/span[13]/span/button
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[1]/div[1]/div[7]/div/div[2]/div/span[13]/span/button').click()
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
                time.sleep(4)

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
                ik = re.sub('^\d\\n', '', i.text)
                print("examining " + ik)
                for j in r:
                    jk = re.sub('^\d\\n', '', j.text)
                    print("comparing " + jk)
                    if jk == phrases[ik]:
                        i.click()
                        j.click()
                        print("match")
                        time.sleep(1)

            time.sleep(8)
            print("done1")
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[3]/div/div[2]/div/button').click()
            time.sleep(8)
            print("done2")
            driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[2]/div/div/div/button').click()
            time.sleep(8)
            print("done3")
            try:
                for i in range(1, 3):
                    driver.find_element("xpath", '/html/body/div[1]/div[1]/div/div/div[2]/div/div/div/button').click()
                    time.sleep(8)
                    print("final %i", i)
            except:
                print("occasional extra screen")
        # Debugging code.

        # except:
        #     pass
        except ElementClickInterceptedException:
            print("Done CIE")
        except NoSuchElementException:
            print("Ok nse")
        except StaleElementReferenceException:
            print("Ok stale")
        except KeyError:
            print("Key error")
        except UnexpectedAlertPresentException:
            print("do nothing")
        except UnexpectedAlertPresentException:
            print("weird")


Duo = Duolingo()
Duo.loginDuo(username, password)

while True:
    Duo.autoXP()
