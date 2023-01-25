import os
import signal
import webview


window = webview.create_window('Escape Room Manager', 'http://localhost:8888')


def on_closing():
  os.kill(os.getppid(), signal.SIGTERM)
  window.destroy()


window.closing += on_closing
webview.start()
