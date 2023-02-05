#!/usr/bin/env python3
import os
import sys
import signal
import webview


def init_window(url, port, name):
  window = webview.create_window(name, '%s:%s' % (url, port,))

  def on_closing():
    if os.name == 'nt':
      os.kill(os.getppid(), signal.CTRL_C_EVENT)
      # window.destroy()
      return

    os.kill(os.getppid(), signal.SIGTERM)
    window.destroy()

  window.events.closing += on_closing
  webview.start()


if __name__ == '__main__':
  _, url, port, name = sys.argv
  init_window(url, port, name)
