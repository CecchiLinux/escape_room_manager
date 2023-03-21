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

  def getChild(self, name, request):
    _reply = {}
    res = -1
    ok_text = None
    if name == b'ping_room':
      res = send_event('ping_room', {})

    if name == b'reset_game':
      ok_text = 'gioco resettato'
      if game_timer.running:
        game_timer.stop()
        res = send_event('timer_stop', {})
      game_timer.reset()
      res = send_event('set_timer', {'minutes': 0})

    if name == b'text_to_room':
      ok_text = 'testo inviato alla stanza'
      _text = request.args[b'text'][0].decode()
      if _text:
        _th = threading.Thread(target=_play_sound, args=('static/audio/mixkit-horror-bell-cartoon-transition-598.wav',))
        _th.start()
      res = send_event('text_to_room', {'text': _text})

    if name == b'timer_start':
      ok_text = 'tempo avviato'
      game_timer.start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if self._is_a_failure(res):
        game_timer.stop()

    if name == b'timer_stop':
      ok_text = 'tempo fermato'
      game_timer.stop()
      res = send_event('timer_stop', {})
      if self._is_a_failure(res):
        game_timer.start()

    if name == b'start_game':
      ok_text = 'partita avviata'
      game_timer.first_start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if self._is_a_failure(res):
        game_timer.stop()

    if name == b'set_timer':
      ok_text = 'timer impostato'
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
          _reply = {'ko': 'stanza non raggiungibile. 1.riavviare stanza; 2.timer stop; 3.timer start'}
        else:
          _reply = {'ko': 'errore'}
      else:
        _reply = {'ok': ok_text or 'comunicazione con stanza ok'}

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
