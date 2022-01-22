from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import getpass
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

   msg = MIMEMultipart()
   msg['From'] = email_user
   msg['To'] = to
   msg['Subject'] = subject
   msg.attach(MIMEText(text))
   if attach:
      part = MIMEBase('application', 'octet-stream')
      part.set_payload(open(attach, 'rb').read())
      Encoders.encode_base64(part)
      part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
      msg.attach(part)
   mailServer = smtplib.SMTP(email_server, 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(email_user, email_pwd)
   mailServer.sendmail(email_user, to, msg.as_string())
   mailServer.close()
