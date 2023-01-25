import os
import signal
import json
from subprocess import Popen
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.python.filepath import FilePath
from twisted.internet import reactor

# ## communication needs
import asyncio
import websockets


WEBSOCKET_SERVER_LOCAL = 'ws://localhost:5000'

#######################################################
# ## communication to the rooms
#
#####################################################


async def event(message):
  async with websockets.connect(WEBSOCKET_SERVER_LOCAL) as websocket:
    message = json.dumps(message)
    print(message)
    await websocket.send(message)
    response = await websocket.recv()
    print(response)
 

def send_event(data):
  print(json.dumps(data))
  asyncio.get_event_loop().run_until_complete(event(data))
  return Resource()


########################################################
# ## Manager UI
#
######################################################

class SendEvent(Resource):

  def getChild(self, name, request):
    print(name)
    if name == b'text_to_room':
      _text = request.args[b'text'][0].decode()
      _d = {
          'event': 'text_to_room',
          'data': {
              'text': _text,
          },
          'timestamp': '',
      }
      return send_event(_d)

    if name == b'start':
      _d = {
          'event': 'start',
          'data': {
              'end_datetime': '',
              'minutes': 60,
          },
          'timestamp': '',
      }
      return send_event(_d)

    send_event({'event': 'hello'})
    return self

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


proc = Popen(
    ['python3', '%s/manager_client.py' % os.path.dirname(os.path.realpath(__file__))],
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
reactor.listenTCP(8888, factory)


def kill_child_process():
  os.kill(proc.pid, signal.SIGTERM)


reactor.addSystemEventTrigger('before', 'shutdown', kill_child_process)
reactor.run()
