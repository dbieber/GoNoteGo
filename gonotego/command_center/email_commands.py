from email import message
import smtplib
import os

from gonotego.command_center import registry
from gonotego.settings import settings

register_command = registry.register_command


@register_command('email {} {}: {}')
def _email(to, subject, text):
  email(to, subject, text)


def email(to, subject, text, attach=None):
  email_user = settings.get('EMAIL_USER')
  email_pwd = settings.get('EMAIL_PASSWORD')
  email_server = settings.get('EMAIL_SERVER') or 'smtp.gmail.com'

  msg = message.EmailMessage()
  msg.set_content(text)

  msg['Subject'] = subject
  msg['From'] = email_user or 'Go-Note-Go@example.com'
  msg['To'] = to
  if email_server and email_pwd:
    server = smtplib.SMTP(email_server, 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(email_user, email_pwd)
  else:
    server = smtplib.SMTP('localhost')
  server.send_message(msg)
  server.quit()
