"""Selenium driver utilities."""


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
    with open('gonotego/uploader/browser/template.js') as f:
      template = f.read()
    js = js.replace('`', r'\`').replace('${', r'\${')
    js = template.replace('<SOURCE>', js)
    return self.driver.execute_script(js)
