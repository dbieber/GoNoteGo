from datetime import datetime
import getpass
import json
import os
import random
import subprocess
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from gonotego.common import events
from gonotego.settings import settings
from gonotego.uploader.blob import blob_uploader
from gonotego.uploader.browser import driver_utils


class RoamBrowser:

  def __init__(self, driver):
    self.driver = driver
    self.utils = driver_utils.DriverUtils(driver)

  def go_home(self):
    self.driver.get('https://roamresearch.com/')

  def go_graph_attempt(self, graph_name):
    if graph_name.startswith('offline/') or graph_name.startswith('app/'):
      graph_url = f'https://roamresearch.com/#/{graph_name}'
    else:
      graph_url = f'https://roamresearch.com/#/app/{graph_name}'
    self.driver.get(graph_url)
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
      except Exception as e:
        print(f'Attempt failed with exception: {repr(e)}')
        time.sleep(1)
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

  def insert_top_level_note(self, text):
    text_json = json.dumps(text)
    js = f'window.insertion_result = insertGoNoteGoNote({text_json});'
    try:
      self.utils.execute_script_tag(js)
    except Exception as e:
      print(f'Failed to insert note: {text}')
      raise e
    time.sleep(0.25)
    return self.get_insertion_result()

  def get_insertion_result(self):
    retries = 5
    while retries:
      try:
        return self.driver.execute_script('return window.insertion_result;')
      except:
        print('Retrying script: window.insertion_result.')
        time.sleep(1)
        retries -= 1

  def create_child_block(self, parent_uid, block, order=-1):
    parent_uid_json = json.dumps(parent_uid)
    block_json = json.dumps(block)
    js = f'window.insertion_result = createChildBlock({parent_uid_json}, {block_json}, {order});'
    self.utils.execute_script_tag(js)
    time.sleep(0.25)
    return self.get_insertion_result()

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

    self.session_uid = None
    self.last_note_uid = None
    self.stack = []

  def get_browser(self):
    if self._browser is not None:
      return self._browser

    options = Options()
    if self.headless:
      options.add_argument('-headless')
    driver = webdriver.Firefox(options=options)
    browser = RoamBrowser(driver)

    # Sign in to Roam.
    username = settings.get('ROAM_USER')
    password = settings.get('ROAM_PASSWORD') or getpass.getpass()
    browser.sign_in(username, password)
    browser.screenshot('screenshot-post-sign-in.png')

    self._browser = browser
    return browser

  def new_session(self):
    browser = self.get_browser()
    time_str = datetime.now().strftime('%H:%M %p')
    block_uid = browser.insert_top_level_note(time_str)
    self.session_uid = block_uid

  def upload(self, note_events):
    browser = self.get_browser()
    browser.go_graph(settings.get('ROAM_GRAPH'))
    time.sleep(0.5)
    browser.screenshot('screenshot-graph-later.png')
    browser.execute_helper_js()

    client = blob_uploader.make_client()
    for note_event in note_events:
      if note_event.action == events.INDENT:
        # When you press tab, that adds your most-recent note to a stack.
        if self.last_note_uid and self.last_note_uid not in self.stack:
          self.stack.append(self.last_note_uid)
      elif note_event.action == events.UNINDENT:
        # When you shift-tab, that pops from the stack.
        if self.stack:
          self.stack.pop()
      elif note_event.action == events.CLEAR_EMPTY:
        # When you shift-delete from an empty note, that clears the stack.
        self.stack = []
      elif note_event.action == events.ENTER_EMPTY:
        # When you submit from an empty note, that pops from the stack.
        if self.stack:
          self.stack.pop()
      elif note_event.action == events.END_SESSION:
        self.end_session()
      elif note_event.action == events.SUBMIT:
        if self.session_uid is None:
          self.new_session()
        text = note_event.text.strip()
        has_audio = note_event.audio_filepath and os.path.exists(note_event.audio_filepath)
        if has_audio:
          text = f'{text} #[[unverified transcription]]'
        if self.stack:
          parent_uid = self.stack[-1]
        else:
          parent_uid = self.session_uid
        block_uid = browser.create_child_block(parent_uid, text)
        self.last_note_uid = block_uid
        print(f'Inserted: "{text}" at block (({block_uid}))')
        if has_audio:
          embed_url = blob_uploader.upload_blob(note_event.audio_filepath, client)
          embed_text = '{{audio: ' + embed_url + '}}'
          print(f'Audio embed: {embed_text}')
          if block_uid:
            browser.create_child_block(block_uid, embed_text)

  def handle_inactivity(self):
    self.end_session()
    self.close_browser()

  def handle_disconnect(self):
    self.end_session()
    self.close_browser()

  def end_session(self):
    self.session_uid = None
    self.last_note_uid = None
    self.stack = []

  def close_browser(self):
    browser = self._browser
    if browser:
      driver = browser.driver
      if driver is not None:
        driver.close()
    self._browser = None

    subprocess.call(['pkill', 'firefox'])
    subprocess.call(['pkill', 'geckodriver'])
