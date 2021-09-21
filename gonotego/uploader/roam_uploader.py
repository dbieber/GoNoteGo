import getpass
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

  def go_graph(self, graph_name):
    self.driver.get(f'https://roamresearch.com/#/app/{graph_name}')

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
      self.sign_in_attempt(username, password)
      retries -= 1

      print(driver.current_url)
      if self.is_element_with_class_name_stable('rm-plan'):
        return True
    print('Failed to sign in. No retries left.')

  def is_element_with_class_name_stable(self, class_name):
    if driver.find_elements_by_class_name(class_name):
      time.sleep(1)
      if driver.find_elements_by_class_name(class_name):
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

  browser.sleep_until_astrolabe_gone()
  time.sleep(1)
  browser.sleep_until_astrolabe_gone()
  print('Graph loaded: ' + driver.current_url)
  browser.screenshot('screenshot-graph.png')

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
