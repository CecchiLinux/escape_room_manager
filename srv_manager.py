import sys
import os
import signal
import json
import threading
import pystache
from playsound import playsound
from subprocess import Popen
from pathlib import Path
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.internet import reactor
from manager_websocket import send_event
from manager_websocket import COMM_ERR_TIMEOUT
from logger import log_info, log_error
from timer import Timer

URL_BASE = 'http://localhost'
PORT = 8888
WINDOW_NAME = 'Escape Room Manager'

_path = os.path.dirname(os.path.realpath(__file__))
_path = os.path.join(_path, '')  # adding '/' or '\'


def load_settings():
  return json.loads(Path('config.json').read_text())


settings = load_settings()
game_timer = Timer(int(settings.get('game_minutes', '60')))


def _spawn_proc(params):
  return Popen(params, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)


########################################################
# ## Control room UI
#
######################################################


def play_sound(sound, label, thread=False):
  def _play_sound(sound):
    return playsound(sound)

  if label not in settings.get('not_muted', []):
    return
  sound = sound.replace('/', os.sep)
  sound = '%s%s' % (_path, sound,)
  if thread:
    _th = threading.Thread(target=_play_sound, args=(sound,))
    _th.start()
  else:
    try:
      _play_sound(sound)
    except Exception:
      pass


class SendEvent(Resource):

  reply = b''

  def render_POST(self, request):
    try:
      res = self.reply.encode('utf-8')
    except Exception:
      res = self.reply
    return res

  def render_GET(self, request):
    return self.render_POST(request)

  def _is_a_failure(self, res):
    if res and res < 0:
      return True
    return False

  def _maybe_stop_timer(self):
    if game_timer.running:
      game_timer.stop()
      return send_event('timer_stop', {})

  def getChild(self, name, request):
    _reply = {}
    res = -1  # failure as default
    str_name = name.decode('utf-8')
    ok_text = settings.get('ok_messages', {}).get(str_name, '')
    ko_text = settings.get('ko_messages', {}).get(str_name, '')

    if name == b'ping_room':
      res = send_event('ping_room', {})

    if name == b'game_success':
      res = self._maybe_stop_timer()
      res = send_event('text_to_room', {'text': settings.get('game_success_text', '')})
      play_sound(settings.get('game_success_audio', ''), str_name, thread=True)

    if name == b'reset_game':
      res = self._maybe_stop_timer()
      game_timer.reset()
      res = send_event('set_timer', {'minutes': 0})
      res = send_event('text_to_room', {'text': ''})

    if name == b'text_to_room':
      _text = request.args[b'text'][0].decode()
      if _text:
        play_sound(settings.get('text_to_room_audio', ''), str_name, thread=True)
      res = send_event('text_to_room', {'text': _text})

    if name == b'timer_start':
      play_sound(settings.get('timer_start_audio', ''), str_name)
      game_timer.start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if self._is_a_failure(res):
        game_timer.stop()
      else:
        deadline = game_timer.get_game_end("%H : %M : %S")
        _reply = {'ok': ok_text, 'deadline': deadline}

    if name == b'timer_stop':
      play_sound(settings.get('timer_stop_audio', ''), str_name)
      res = self._maybe_stop_timer()
      if self._is_a_failure(res):
        game_timer.start()

    if name == b'start_game':
      play_sound(settings.get('start_game_audio', ''), str_name)
      game_timer.first_start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if self._is_a_failure(res):
        game_timer.stop()
      else:
        deadline = game_timer.get_game_end("%H : %M : %S")
        _reply = {'ok': ok_text, 'deadline': deadline}

    if name == b'set_timer':
      _minutes = int(request.args[b'minutes'][0].decode())
      game_timer.first_start(_minutes, false_start=True)
      res = send_event('set_timer', {'minutes': _minutes})

    if name == b'start_room':
      # ## if there's alredy an acrive room, fail
      res = send_event('ping_room', {})
      if self._is_a_failure(res):
        proc_room = _spawn_proc(['python', '%ssrv_room.py' % _path])
        _reply = {'ok': ok_text}
      else:
        _reply = {'ko': ko_text}
    
    if name == b'is_game_finished':
      _reply = {'ok': ok_text, 'status': 'running'}
      if game_timer.running:
        if game_timer.get_time_left().total_seconds() <= 0:
          _reply = {'ok': 'gioco finito', 'status': 'finished'}
          game_timer.finish_game()
          res = send_event('text_to_room', {'text': settings.get('time_up_text', '')})
          play_sound(settings.get('time_up_audio', ''), "time_up", thread=True)

    if not _reply:  # if the reply was not set yet
      if self._is_a_failure(res):
        if res == COMM_ERR_TIMEOUT:
          _reply = {'ko': settings.get('ko_room_connection_text', '')}
        else:
          _reply = {'ko': settings.get('ko_generic_text', '')}
      else:
        _reply = {'ok': ok_text or settings.get('ok_room_connection_text', '')}

    self.reply = json.dumps(_reply)
    return self


class Html(Resource):
  isLeaf = True

  def render_GET(self, request):
    _d = {
        'room_texts': [{'text': _v} for _v in settings.get('room_texts', [])]
    }
    tmpl = open('static/html/app.xhtml').read()
    html = pystache.render(tmpl, _d)
    return html.encode()


def main(start_broker):
  _path = os.path.dirname(os.path.realpath(__file__))
  _path = os.path.join(_path, '')  # adding '/' or '\'

  proc_window = _spawn_proc(['python', '%swindow.py' % _path, URL_BASE, str(PORT), WINDOW_NAME])

  if start_broker:
    proc_broker = _spawn_proc(['python', '%ssrv_message_broker.py' % _path])
  
  root = Resource()
  root.putChild(b'', Html())
  root.putChild(b'event', SendEvent())
  root.putChild(b'static', File('static'))
  factory = Site(root)
  reactor.listenTCP(PORT, factory)

  def kill_child_process():
    def _kill_child_process(pid):
      try:
        os.kill(pid, signal.SIGTERM)
      except Exception:
        print("already closed")
    _kill_child_process(proc_window.pid)
    if start_broker:
      _kill_child_process(proc_broker.pid)

  reactor.addSystemEventTrigger('before', 'shutdown', kill_child_process)
  reactor.run()


if __name__ == "__main__":
  _, start_broker = sys.argv
  main(int(start_broker))
