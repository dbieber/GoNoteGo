import getpass
import random
import subprocess
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader


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


class IdeaflowBrowser:

  def __init__(self, driver):
    self.driver = driver
    self.utils = DriverUtils(driver)

  def go_home(self):
    self.driver.get('https://ideaflow.app/')

  def sign_in_attempt(self, username, password):
    """Sign in to Roam Research."""
    driver = self.driver
    driver.get('https://ideaflow.app/')
    login_el = self.utils.find_element_by_text('Log in')
    login_el.click()
    username_el = driver.find_element_by_name('username')
    username_el.clear()
    username_el.send_keys(username)
    password_el = driver.find_element_by_name('password')
    password_el.clear()
    password_el.send_keys(password)
    self.screenshot('screenshot-signing-in.png')
    password_el.send_keys(Keys.RETURN)
    time.sleep(5.0)

  def sign_in(self, username, password, retries=5):
    """Sign in to Roam Research with retries."""
    while retries > 0:
      print('Attempting sign in.')
      retries -= 1
      try:
        self.sign_in_attempt(username, password)
      except Exception as e:
        print(f'Attempt failed with exception: {repr(e)}')
        time.sleep(1)
    print('Failed to sign in. No retries left.')
    return False

  def screenshot(self, name=None):
    filename = name or 'screenshot.png'
    print(f'Saving screenshot to {filename}')
    try:
      self.driver.save_screenshot(filename)
    except:
      print('Failed to save screenshot. Continuing.')


class Uploader:

  def __init__(self, headless=True):
    self.headless = headless
    self._browser = None

  def get_browser(self):
    if self._browser is not None:
      return self._browser

    options = Options()
    if self.headless:
      options.add_argument('-headless')
    driver = webdriver.Firefox(options=options)
    browser = RoamBrowser(driver)

    # Sign in to Roam.
    username = secure_settings.ROAM_USER
    password = secure_settings.ROAM_PASSWORD or getpass.getpass()
    browser.sign_in(username, password)
    browser.screenshot('screenshot-post-sign-in.png')

    self._browser = browser
    return browser

  def upload(self, note_events):
    browser = self.get_browser()
    browser.go_graph(secure_settings.ROAM_GRAPH)
    time.sleep(0.5)
    browser.screenshot('screenshot-graph-later.png')

    browser.execute_helper_js()
    client = blob_uploader.make_client()
    for note_event in note_events:
      text = note_event.text.strip()
      if note_event.audio_filepath:
        text = f'{text} #[[unverified transcription]]'
      block_uid = browser.insert_note(text)
      print(f'Inserted: "{text}" at block (({block_uid}))')
      if note_event.audio_filepath:
        embed_url = blob_uploader.upload_blob(note_event.audio_filepath, client)
        embed_text = '{{audio: ' + embed_url + '}}'
        print(f'Audio embed: {embed_text}')
        if block_uid:
          browser.create_child_block(block_uid, embed_text)

  def handle_inactivity(self):
    self.close_browser()

  def handle_disconnect(self):
    self.close_browser()

  def close_browser(self):
    browser = self._browser
    if browser:
      driver = browser.driver
      if driver is not None:
        driver.close()
    self._browser = None

    subprocess.call(['pkill', 'firefox'])
    subprocess.call(['pkill', 'geckodriver'])
