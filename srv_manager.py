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


COMM_ROOM_TIMEOUT = 2
WEBSOCKET_SERVER_LOCAL = 'ws://localhost:5000'

#######################################################
# ## communication to the rooms
#
#####################################################


async def wait_room_reply(ws):
  response = await ws.recv()  # wait for client
  return response


async def event(message):
  async with websockets.connect(WEBSOCKET_SERVER_LOCAL) as ws:
    message = json.dumps(message)
    print(f'send message to broker: {message}')
    await ws.send(message)
    print('broker confirmed')
    res = await ws.recv()
    print(f'message from broker: {res}')
    try:
      res = await asyncio.wait_for(wait_room_reply(ws), timeout=COMM_ROOM_TIMEOUT)
      # response = await ws.recv()  # wait for client
      print(f'message from room: {res}')
    except asyncio.exceptions.TimeoutError as exc:
      print('timeout!')
      log_error(str(exc))
      print('can\'t communicate with the room')
    print('exit')
 

def send_event(data):
  try:
    asyncio.get_event_loop().run_until_complete(event(data))
  except Exception as exc:
    log_error(str(exc))
    # raise ss
    return -1


########################################################
# ## Manager UI
#
######################################################

URL_BASE = 'http://localhost'
PORT = 8888
WINDOW_NAME = 'Escape Room Manager'


class SendEvent(Resource):

  def getChild(self, name, request):
    res = -1
    if name == b'text_to_room':
      _text = request.args[b'text'][0].decode()
      _d = {'event': 'text_to_room', 'data': {'text': _text}, 'timestamp': ''}
      res = send_event(_d)

    if name == b'timer_start':
      game_timer.start()
      deadline = game_timer.get_game_end()
      _d = {'event': 'start_game', 'data': {'deadline': deadline}, 'timestamp': ''}
      res = send_event(_d)

    if name == b'timer_stop':
      game_timer.stop()
      _d = {'event': 'timer_stop', 'data': {}, 'timestamp': ''}
      res = send_event(_d)

    if name == b'start_game':
      game_timer.first_start()
      deadline = game_timer.get_game_end()
      _d = {'event': 'start_game', 'data': {'deadline': deadline}, 'timestamp': ''}
      res = send_event(_d)

    if res == -1:
      log_error("cannot contact the broker")
      return Resource()  # maybe return self
    return Resource()  # maybe return self

  def render_POST(self, request):
    _at = request.prepath 
    output = f'Hello, world! I am located at {_at}.'
    return output.encode('utf8')

  def render_GET(self, request):
    return self.render_POST(request)


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

proc = Popen(
    ['python3', '%s/window.py' % os.path.dirname(os.path.realpath(__file__)), URL_BASE, str(PORT), WINDOW_NAME],
    shell=False,
    stdin=None,
    stdout=None,
    stderr=None,
    close_fds=True
)

root = Resource()
root.putChild(b'', Html())
root.putChild(b'event', SendEvent())
root.putChild(b'static', File('static'))
factory = Site(root)
reactor.listenTCP(PORT, factory)


def kill_child_process():
  os.kill(proc.pid, signal.SIGTERM)


reactor.addSystemEventTrigger('before', 'shutdown', kill_child_process)
reactor.run()
