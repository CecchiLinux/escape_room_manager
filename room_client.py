import os
import signal
import webview


window = webview.create_window('Escape Room Client', 'http://localhost:8889')


def on_closing():
  os.kill(os.getppid(), signal.SIGTERM)
  window.destroy()


window.closing += on_closing
webview.start()
