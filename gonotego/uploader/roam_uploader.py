import getpass
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from gonotego.settings import secure_settings


class DriverUtils:

  def __init__(self, driver):
    self.driver = driver

  def find_element_by_text_exact(self, text):
    return self.driver.find_element_by_xpath(f"//*[text()='{text}']")

  def find_elements_by_text_exact(self, text):
    assert "'" not in text
    return self.driver.find_elements_by_xpath(f"//*[text()='{text}']")

  def find_element_by_text(self, text):
    return self.driver.find_element_by_xpath(f"//*[contains(text(),'{text}')]")

  def find_elements_by_text(self, text):
    assert "'" not in text
    return self.driver.find_elements_by_xpath(f"//*[contains(text(),'{text}')]")

  def execute_script_tag(self, js):
    with open('gonotego/uploader/roam/template.js') as f:
      template = f.read()
    js = js.replace('`', r'\`').replace('${', r'\${')
    js = template.replace('<SOURCE>', js)
    return self.driver.execute_script(js)


class RoamBrowser:

  def __init__(self, driver):
    self.driver = driver
    self.utils = DriverUtils(driver)

  def go_home(self):
    self.driver.get('https://roamresearch.com/')

  def go_graph(self, graph_name):
    self.driver.get(f'https://roamresearch.com/#/app/{graph_name}')

  def sign_in(self, username, password):
    """Sign in to Roam Research."""
    driver = self.driver
    driver.get('https://roamresearch.com/#/signin')
    time.sleep(0.25)
    email_el = driver.find_element_by_name('email')
    email_el.clear()
    email_el.send_keys(username)
    password_el = driver.find_element_by_name('password')
    password_el.clear()
    password_el.send_keys(password)
    password_el.send_keys(Keys.RETURN)
    time.sleep(1.0)

  def screenshot(self, name=None):
    filename = name or 'screenshot.png'
    self.driver.save_screenshot(filename)

  def sleep(self):
    seconds = random.randint(10, 160)
    time.sleep(seconds)

  def execute_helper_js(self):
    with open('gonotego/uploader/roam/helper.js', 'r') as f:
      js = f.read()
    self.utils.execute_script_tag(js)

  def insert_note(self, text):
    text = text.replace('`', r'\`').replace('${', r'\${')
    js = f'insertGoNoteGoNote(`{text}`)'
    self.utils.execute_script_tag(js)


def upload(note_events, headless=True):
  options = Options()
  if headless:
    options.add_argument('-headless')
  driver = webdriver.Firefox(options=options)
  browser = RoamBrowser(driver)

  username = secure_settings.ROAM_USER
  password = secure_settings.ROAM_PASSWORD or getpass.getpass()
  browser.sign_in(username, password)
  browser.screenshot('screenshot-post-sign-in.png')
  browser.go_graph(secure_settings.ROAM_GRAPH)

  # Wait for graph to load.
  def wait_for_graph_to_load():
    retries = 20
    loaded = False

    # First wait for rm-sync to appear.
    while retries > 0:
      try:
        driver.find_elements_by_class_name('rm-sync')
        print('sync found')
        loaded = True
        break  # Once found, exit the loop.
      except:
        print('sync not found')
        pass
      time.sleep(1)
      retries -= 1

    # Also wait for loading-astrolabe to disappear.
    retries = 20
    loaded = False
    while retries > 0:
      if driver.find_elements_by_class_name('loading-astrolabe'):
        print('Astrolabe still there.')
        print(driver.find_elements_by_class_name('loading-astrolabe'))
        browser.screenshot('screenshot-astrolabe.png')
      else:
        print('Astrolabe gone')
        loaded = True
        break  # Once gone, exit the loop.
      time.sleep(1)
      retries -= 1

    if not loaded:
      browser.screenshot('screenshot-raising.png')
      raise ValueError('Could not write notes.')

  wait_for_graph_to_load()
  time.sleep(1)
  wait_for_graph_to_load()
  print('Graph loaded')
  browser.screenshot('screenshot-graph.png')

  browser.execute_helper_js()
  time.sleep(0.5)
  for note_event in note_events:
    text = note_event.text.strip()
    if note_event.audio_filepath:
      text = f'{text} #[[Unverified transcription]]'
    browser.insert_note(text)
    print(f'Inserted: {text}')

  time.sleep(1)
  print('Screenshot')
  browser.screenshot('screenshot-closing.png')
  print('Closing browser')
  driver.close()


def main():
  import getpass
  import time

  from selenium import webdriver
  from selenium.webdriver.common.by import By
  from selenium.webdriver.common.keys import Keys
  from selenium.webdriver.firefox.options import Options
  from gonotego.uploader import roam_uploader
  headless = False
  options = roam_uploader.Options()

  if headless:
    options.add_argument('-headless')
  driver = roam_uploader.webdriver.Firefox(options=options)
  browser = roam_uploader.RoamBrowser(driver)

  username = secure_settings.ROAM_USER
  password = secure_settings.ROAM_PASSWORD or getpass.getpass()
  browser.sign_in(username, password)
  browser.go_graph(secure_settings.ROAM_GRAPH)

  browser.execute_helper_js()
  time.sleep(0.05)
  browser.insert_note("It's working!!!")
