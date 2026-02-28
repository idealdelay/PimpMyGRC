# Copyright 2009-2016 Free Software Foundation, Inc.
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-2.0-or-later
#

from gi.repository import Gtk
import argparse
import logging
import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')


VERSION_AND_DISCLAIMER_TEMPLATE = """\
GNU Radio Companion %s

This program is part of GNU Radio
GRC comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it.
"""

LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

from gi.repository import Gdk

css = b"""
/* Cursor */
entry, textview {
    caret-color: #000000;
    -gtk-secondary-caret-color: #000000;
}

/* Force selection colors (covers more GTK node layouts) */
entry selection,
entry text selection,
textview selection,
textview text selection,
* selection {
    background-color: #FF3300;   /* cyberpunk red selection */
    color: #000000;
}

/* Also cover focus cases */
entry:focus selection,
entry:focus text selection,
textview:focus selection,
textview:focus text selection {
    background-color: #ff2ea6;
    color: #000000;
}
"""



provider = Gtk.CssProvider()
provider.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    provider,
    Gtk.STYLE_PROVIDER_PRIORITY_USER
)

# Toolbar CSS theming (reads config directly — no gui package import at module level)
try:
    import json as _json
    from pathlib import Path as _Path
    _fx_path = _Path.home() / ".gnuradio" / "grc_effects.json"
    _toolbar_on = True  # default
    if _fx_path.is_file():
        with open(_fx_path) as _f:
            _fx = _json.load(_f)
        _toolbar_on = _fx.get('toolbar_css', True)
    if _toolbar_on:
        _toolbar_css = b"""
headerbar, .titlebar {
    background-color: #1A0A0A; color: #FFCCCC;
    border-bottom: 1px solid #FF4444;
}
menubar, menubar > menuitem {
    background-color: #1A0A0A; color: #FFCCCC;
}
menubar > menuitem:hover { background-color: #FF4444; }
menu, .context-menu {
    background-color: #1A0A0A; color: #FFCCCC;
    border: 1px solid #FF4444;
}
menu menuitem:hover { background-color: #FF4444; }
toolbar, .toolbar {
    background-color: #1A0A0A; color: #FFCCCC;
    border-bottom: 1px solid #FF4444;
}
toolbar button { color: #FFCCCC; background: transparent; }
toolbar button:hover { background-color: #FF4444; }
"""
        _tp = Gtk.CssProvider()
        _tp.load_from_data(_toolbar_css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), _tp,
            Gtk.STYLE_PROVIDER_PRIORITY_USER)
except Exception:
    pass


def main():
    from gnuradio import gr
    parser = argparse.ArgumentParser(
        description=VERSION_AND_DISCLAIMER_TEMPLATE % gr.version())
    parser.add_argument('flow_graphs', nargs='*')
    parser.add_argument(
        '--log', choices=['debug', 'info', 'warning', 'error', 'critical'], default='warning')
    args = parser.parse_args()

    # Enable logging
    # Note: All other modules need to use the 'grc.<module>' convention
    log = logging.getLogger('grc')
    # NOTE: This sets the log level to what was requested for the logger on the
    # command line, but this may not be the correct approach if multiple handlers
    # are intended to be used. The logger level shown here indicates all the log
    # messages that are captured and the handler levels indicate messages each
    # handler will output. A better approach may be resetting this to logging.DEBUG
    # to catch everything and making sure the handlers have the correct levels set.
    # This would be useful for a future GUI logging window that can filter messages
    # independently of the console output. In this case, this should be DEBUG.
    log.setLevel(LOG_LEVELS[args.log])

    # Console formatting
    console = logging.StreamHandler()
    console.setLevel(LOG_LEVELS[args.log])

    #msg_format = '[%(asctime)s - %(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)'
    msg_format = '[%(levelname)s] %(message)s (%(filename)s:%(lineno)s)'
    date_format = '%I:%M'
    formatter = logging.Formatter(msg_format, datefmt=date_format)

    #formatter = utils.log.ConsoleFormatter()
    console.setFormatter(formatter)
    log.addHandler(console)

    py_version = sys.version.split()[0]
    log.debug("Starting GNU Radio Companion ({})".format(py_version))

    # Delay importing until the logging is setup
    from .gui.Platform import Platform
    from .gui.Application import Application

    log.debug("Loading platform")
    platform = Platform(
        version=gr.version(),
        version_parts=(gr.major_version(), gr.api_version(),
                       gr.minor_version()),
        prefs=gr.prefs(),
        install_prefix=gr.prefix()
    )
    platform.build_library()

    log.debug("Loading application")
    app = Application(args.flow_graphs, platform)
    log.debug("Running")
    sys.exit(app.run())
