import inspect
import os

from flask import Flask, request, redirect, send_from_directory, render_template

from gonotego.settings import settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    static_url_path='/static',
    template_folder=STATIC_DIR,
)


@app.route('/')
def index():
  fields = []
  setting_keys = [
      attr[0] for attr in inspect.getmembers(settings.secure_settings, lambda a: not inspect.isroutine(a))
      if not attr[0].startswith('_')
  ]
  for setting_key in setting_keys:
    try:
      value = settings.get(setting_key)
    except:
      value = 'ERROR'
    field = {
        'id': setting_key,
        'name': setting_key,
        'label': setting_key,
        'value': value,
        'type': 'text',
    }
    fields.append(field)
  return render_template('form.html', fields=fields)


@app.route('/submit', methods=['POST'])
def handle_submit():
  for setting_key, value in request.form.items():
    old_value = settings.get(setting_key)
    if value != old_value:
      settings.set(setting_key, value)
  return redirect('/')


if __name__ == '__main__':
  app.run(port=5002)
