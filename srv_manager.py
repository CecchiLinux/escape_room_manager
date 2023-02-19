import sys
import os
import signal
import json
from subprocess import Popen
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.python.filepath import FilePath
from twisted.internet import reactor
from logger import log_info, log_error
from timer import Timer

# ## communication needs
import asyncio
import websockets


WEBSOCKET_SERVER_LOCAL = 'ws://localhost:5000'

#######################################################
# ## communication to the rooms
#
#####################################################

COMM_ROOM_TIMEOUT = 2
COMM_ERR_GENERIC = -10
COMM_ERR_TIMEOUT = -20


async def wait_room_reply(ws):
  response = await ws.recv()  # wait for room confirmation
  return response


async def event(message):
  '''
    - create a connection to the broker
    - wait for broker confirm
    - wait for a single room confirm (timeout)
    - close the connection
  '''
  async with websockets.connect(WEBSOCKET_SERVER_LOCAL) as ws:
    message = json.dumps(message)
    print(f'send message to broker: {message}')
    await ws.send(message)
    # print('broker confirmed')
    res = await ws.recv()  # await reply from broker
    print(f'message from broker: {res}')
    try:
      res = await asyncio.wait_for(wait_room_reply(ws), timeout=COMM_ROOM_TIMEOUT)  # await reply from room
      print(f'message from room: {res}')
    except asyncio.exceptions.TimeoutError as exc:
      raise exc
    print('exit')
 

def send_event(event_name, data):
  _d = {'event': event_name, 'data': data, 'sender': 'manager', 'timestamp': ''}
  try:
    asyncio.get_event_loop().run_until_complete(event(_d))
  except asyncio.exceptions.TimeoutError as exc:
    print(str(exc))
    log_error('room timeout! Can\'t communicate with the room')
    return COMM_ERR_TIMEOUT
  except Exception as exc:
    log_error(str(exc))
    return COMM_ERR_GENERIC


########################################################
# ## Manager UI
#
######################################################

URL_BASE = 'http://localhost'
PORT = 8888
WINDOW_NAME = 'Escape Room Manager'


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

  def getChild(self, name, request):
    _reply = {'ok': ''}
    res = -1
    if name == b'ping_room':
      res = send_event('ping_room', {})

    if name == b'text_to_room':
      _text = request.args[b'text'][0].decode()
      res = send_event('text_to_room', {'text': _text})

    if name == b'timer_start':
      game_timer.start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if res and res < 0:
        game_timer.stop()

    if name == b'timer_stop':
      game_timer.stop()
      res = send_event('timer_stop', {})
      if res and res < 0:
        game_timer.start()

    if name == b'start_game':
      game_timer.first_start()
      deadline = game_timer.get_game_end()
      res = send_event('start_game', {'deadline': deadline})
      if res and res < 0:
        game_timer.stop()

    if res and res < 0:
      if res == COMM_ERR_TIMEOUT:
        _reply = {'ko': 'cannot contact the room'}
      _reply = {'ko': 'error'}
    else:
      _reply = {'ok': 'done'}

    self.reply = json.dumps(_reply)
    return self


class Html(Resource):
  isLeaf = True

  def render_GET(self, request):
    return FilePath('static/html/app.xhtml').getContent()


def load_settings():
  return {
      'game_minutes': 60,
  }


settings = load_settings()
game_timer = Timer(settings['game_minutes'])


def main(start_broker):
  _path = os.path.dirname(os.path.realpath(__file__))
  _path = os.path.join(_path, '')  # adding '/' or '\'

  def _spawn_proc(params):
    return Popen(params, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)

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
