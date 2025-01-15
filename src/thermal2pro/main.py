#!/usr/bin/env python3
import gi
try:
    gi.require_version('Gtk', '4.0')
except ValueError:
    gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from thermal2pro.ui.window import ThermalWindow

class ThermalApp(Gtk.Application):
    def __init__(self):
        super().__init__()

    def do_activate(self):
        win = ThermalWindow(self)
        win.present()

def main():
    app = ThermalApp()
    return app.run(None)

if __name__ == "__main__":
    main()
