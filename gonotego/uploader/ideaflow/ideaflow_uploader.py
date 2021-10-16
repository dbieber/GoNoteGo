import getpass
import subprocess
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader
from gonotego.uploader.browser import driver_utils


class IdeaflowBrowser:

  def __init__(self, driver):
    self.driver = driver
    self.utils = driver_utils.DriverUtils(driver)

  def go_home(self):
    self.driver.get('https://ideaflow.app/')

  def sign_in_attempt(self, username, password):
    """Sign in to Ideaflow."""
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
    """Sign in to Ideaflow with retries."""
    while retries > 0:
      print('Attempting sign in.')
      retries -= 1
      try:
        self.sign_in_attempt(username, password)
        if self.driver.find_element_by_css_selector('[role=presentation]'):
          return True
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
    browser = IdeaflowBrowser(driver)

    # Sign in to Ideaflow.
    username = secure_settings.IDEAFLOW_USER
    password = secure_settings.IDEAFLOW_PASSWORD or getpass.getpass()
    browser.sign_in(username, password)
    browser.screenshot('screenshot-post-sign-in.png')

    self._browser = browser
    return browser

  def upload(self, note_events):
    browser = self.get_browser()

    client = blob_uploader.make_client()
    for note_event in note_events:
      text = note_event.text.strip()
      if note_event.audio_filepath:
        audio_url = blob_uploader.upload_blob(note_event.audio_filepath, client)
        text = f'{text} #unverified-transcription ({audio_url})'
      browser.insert_note(text)

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
