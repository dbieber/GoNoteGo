import getpass
import random
import subprocess
import time

import dropbox

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

  def go_graph_attempt(self, graph_name):
    self.driver.get(f'https://roamresearch.com/#/app/{graph_name}')
    self.sleep_until_astrolabe_gone()
    time.sleep(1)
    self.sleep_until_astrolabe_gone()
    print('Graph loaded: ' + self.driver.current_url)
    self.screenshot('screenshot-graph.png')

  def go_graph(self, graph_name, retries=5):
    while retries > 0:
      print('Attempting to go to graph.')
      self.go_graph_attempt(graph_name)
      retries -= 1

      print(self.driver.current_url)
      if self.is_element_with_class_name_stable('roam-app'):
        return True
    print('Failed to go to graph. No retries left.')
    return False

  def sign_in_attempt(self, username, password):
    """Sign in to Roam Research."""
    driver = self.driver
    driver.get('https://roamresearch.com/#/signin')
    email_el = driver.find_element_by_name('email')
    email_el.clear()
    email_el.send_keys(username)
    password_el = driver.find_element_by_name('password')
    password_el.clear()
    password_el.send_keys(password)
    self.screenshot('screenshot-signing-in.png')
    password_el.send_keys(Keys.RETURN)
    time.sleep(5.0)
    self.sleep_until_astrolabe_gone()

  def sign_in(self, username, password, retries=5):
    """Sign in to Roam Research with retries."""
    while retries > 0:
      print('Attempting sign in.')
      retries -= 1
      try:
        self.sign_in_attempt(username, password)

        print(self.driver.current_url)
        if self.is_element_with_class_name_stable('rm-plan'):
          return True
      except:
        print('Attempt failed with exception.')
    print('Failed to sign in. No retries left.')
    return False

  def is_element_with_class_name_stable(self, class_name):
    if self.driver.find_elements_by_class_name(class_name):
      time.sleep(1)
      if self.driver.find_elements_by_class_name(class_name):
        return True
    return False

  def screenshot(self, name=None):
    filename = name or 'screenshot.png'
    print(f'Saving screenshot to {filename}')
    try:
      self.driver.save_screenshot(filename)
    except:
      print('Failed to save screenshot. Continuing.')

  def sleep(self):
    seconds = random.randint(10, 160)
    time.sleep(seconds)

  def execute_helper_js(self):
    with open('gonotego/uploader/roam/helper.js', 'r') as f:
      js = f.read()
    self.utils.execute_script_tag(js)

  def insert_note(self, text):
    text = text.replace('`', r'\`').replace('${', r'\${')
    js = f'window.insertion_result = insertGoNoteGoNote(`{text}`);'
    self.utils.execute_script_tag(js)
    time.sleep(0.25)
    retries = 5
    while retries:
      try:
        return self.driver.execute_script('return window.insertion_result;');
      except:
        print('Retrying script: window.insertion_result.')
        time.sleep(1)
        retries -= 1

  def create_child_block(self, parent_uid, block, order=-1):
    parent_uid = parent_uid.replace('`', r'\`').replace('${', r'\${')
    block = block.replace('`', r'\`').replace('${', r'\${')
    js = f'window.insertion_result = createChildBlock(`{parent_uid}`, `{block}`, {order});'
    self.utils.execute_script_tag(js)

  def sleep_until_astrolabe_gone(self, timeout=30):
    while self.driver.find_elements_by_class_name('loading-astrolabe'):
      print('Astrolabe still there.')
      time.sleep(1)
      timeout -= 1
      if timeout <= 0:
        raise RuntimeError('Astrolabe still there after timeout.')
    print('Astrolabe gone.')


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
    driver = browser.driver

    browser.go_graph(secure_settings.ROAM_GRAPH)
    time.sleep(0.5)
    browser.screenshot('screenshot-graph-later.png')

    browser.execute_helper_js()
    dbx = dropbox.Dropbox(secure_settings.DROPBOX_ACCESS_TOKEN)
    for note_event in note_events:
      text = note_event.text.strip()
      if note_event.audio_filepath:
        text = f'{text} #[[unverified transcription]]'
      block_uid = browser.insert_note(text)
      print(f'Inserted: "{text}" at block (({block_uid}))')
      if note_event.audio_filepath:
        dropbox_path = f'/{note_event.audio_filepath}'
        with open(note_event.audio_filepath, 'rb') as f:
          file_metadata = dbx.files_upload(f.read(), dropbox_path)
          link_metadata = dbx.sharing_create_shared_link(dropbox_path)
          embed_url = link_metadata.url.replace('www.', 'dl.').replace('?dl=0', '')
          embed_text = '{{audio: ' + embed_url + '}}'
          print(f'Audio embed: {embed_text}')
          if block_uid:
            browser.create_child_block(block_uid, embed_text)

  def close_browser(self):
    browser = self._browser
    driver = browser.driver
    if driver is not None:
      driver.close()
    self._browser = None

    subprocess.call(['pkill', 'firefox'])
    subprocess.call(['pkill', 'geckodriver'])
