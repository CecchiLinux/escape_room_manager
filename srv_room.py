import os
import signal
from subprocess import Popen
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.python.filepath import FilePath
from twisted.internet import reactor


OPEN_IN_WINDOW = True

URL_BASE = 'http://localhost'
PORT = 8889
WINDOW_NAME = 'Escape Room Client'


########################################################
# ## Room UI
#
######################################################

class Html(Resource):
  isLeaf = True

  def render_GET(self, request):
    return FilePath('static/html/room_app.xhtml').getContent()


def main():
  if OPEN_IN_WINDOW:
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
  root.putChild(b'static', File('static'))
  factory = Site(root)
  reactor.listenTCP(PORT, factory)

  if OPEN_IN_WINDOW:

    def kill_child_process():
      os.kill(proc.pid, signal.SIGTERM)
    reactor.addSystemEventTrigger('before', 'shutdown', kill_child_process)

  reactor.run()


if __name__ == "__main__":
  main()
