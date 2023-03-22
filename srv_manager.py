import sys
import os
import signal
import json
import threading
from playsound import playsound
from subprocess import Popen
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.python.filepath import FilePath
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
  return {
      'game_minutes': 60,
      'text_to_room_audio': 'static/audio/mixkit-horror-bell-cartoon-transition-598.wav',
      'ok_messages': {
          'game_success': 'vittoria!!!',
          'reset_game': 'gioco resettato',
          'text_to_room': 'testo inviato alla stanza',
          'timer_start': 'tempo avviato',
          'timer_stop': 'tempo fermato',
          'start_game': 'partita avviata',
          'set_timer': 'timer impostato',
      },
      'game_success_text': 'Congratulazioni, siete usciti dalla stanza!!!',
      'ko_room_connection_text': 'stanza non raggiungibile. 1.riavviare stanza; 2.timer stop; 3.timer start',
      'ko_generic_text': 'errore',
      'ok_room_connection_text': 'comunicazione con stanza ok',
  }


settings = load_settings()
game_timer = Timer(settings['game_minutes'])


def _spawn_proc(params):
  return Popen(params, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)


########################################################
# ## Control room UI
#
######################################################


def _play_sound(sound):
  return playsound('%s%s' % (_path, sound,))


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
    ok_text = settings['ok_messages'].get(name.decode('utf-8'), '')
    ko_text = ''

    if name == b'ping_room':
      res = send_event('ping_room', {})

    if name == b'game_success':
      res = self._maybe_stop_timer()
      res = send_event('text_to_room', {'text': settings['game_success_text']})

    if name == b'reset_game':
      res = self._maybe_stop_timer()
      game_timer.reset()
      res = send_event('set_timer', {'minutes': 0})
      res = send_event('text_to_room', {'text': 'Benvenuti'})

    if name == b'text_to_room':
      _text = request.args[b'text'][0].decode()
      if _text:
        _th = threading.Thread(target=_play_sound, args=(settings['text_to_room_audio'],))
        _th.start()
      res = send_event('text_to_room', {'text': _text})

    if name == b'timer_start':
      game_timer.start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if self._is_a_failure(res):
        game_timer.stop()

    if name == b'timer_stop':
      res = self._maybe_stop_timer()
      if self._is_a_failure(res):
        game_timer.start()

    if name == b'start_game':
      game_timer.first_start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if self._is_a_failure(res):
        game_timer.stop()

    if name == b'set_timer':
      _minutes = int(request.args[b'minutes'][0].decode())
      game_timer.first_start(_minutes, false_start=True)
      res = send_event('set_timer', {'minutes': _minutes})

    if name == b'start_room':
      # ## if there's alredy an acrive room, fail
      res = send_event('ping_room', {})
      if self._is_a_failure(res):
        proc_room = _spawn_proc(['python', '%ssrv_room.py' % _path])
        _reply = {'ok': 'stanza avviata'}
      else:
        _reply = {'ko': 'stanza già avviata, controlla tra le finestre aperte'}
    
    if name == b'is_game_finished':
      _reply = {'ok': 'gioco in corso', 'status': 'running'}
      if game_timer.running:
        if game_timer.get_time_left().total_seconds() <= 0:
          _reply = {'ok': 'gioco finito', 'status': 'finished'}
          game_timer.finish_game()
          res = send_event('text_to_room', {'text': 'Tempo scaduto'})

    if not _reply:  # if the reply was not already set
      if self._is_a_failure(res):
        if res == COMM_ERR_TIMEOUT:
          _reply = {'ko': settings['ko_room_connection_text']}
        else:
          _reply = {'ko': settings['ko_generic_text']}
      else:
        _reply = {'ok': ok_text or settings['ok_room_connection_text']}

    self.reply = json.dumps(_reply)
    return self


class Html(Resource):
  isLeaf = True

  def render_GET(self, request):
    return FilePath('static/html/app.xhtml').getContent()


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
