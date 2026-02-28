"""
Copyright 2008,2013 Free Software Foundation, Inc.
This file is part of GNU Radio

SPDX-License-Identifier: GPL-2.0-or-later

"""


from gi.repository import Gtk, Gdk, cairo
# import pycairo

from .. import Constants


def get_color(color_code):
    color = Gdk.RGBA()
    color.parse(color_code)
    return color.red, color.green, color.blue, color.alpha

#################################################################################
# fg colors — Cyberpunk Red theme
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFD700')  # Gold / white-hot

BORDER_COLOR = get_color('#660000')     # Dark red border

BORDER_COLOR_DISABLED = get_color('#704040')

FONT_COLOR = get_color('#FF4444')       # Red text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#3A0A0A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF2200')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#2A2A00')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#AAAA00')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#1E0C0C')  # Dark crimson

COMMENT_BACKGROUND_COLOR = get_color('#0E0808')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#1A0808')    # Dark crimson

BLOCK_DISABLED_COLOR = get_color('#231414')

BLOCK_BYPASSED_COLOR = get_color('#1A1A00')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#FFB300')  # Gold wires

CONNECTION_DISABLED_COLOR = get_color('#442626')

CONNECTION_ERROR_COLOR = get_color('#FF0000')


DEFAULT_DOMAIN_COLOR = get_color('#FFB300')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — cyberpunk red shades
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'sparks'
AMBIENT_PARTICLE_COLOR = '#FF4400'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #CC2222; }
                         #dtype_real            { background-color: #FF6644; }
                         #dtype_float           { background-color: #FF6644; }
                         #dtype_int             { background-color: #FFB300; }

                         #dtype_complex_vector  { background-color: #AA1818; }
                         #dtype_real_vector     { background-color: #CC4433; }
                         #dtype_float_vector    { background-color: #CC4433; }
                         #dtype_int_vector      { background-color: #CC8800; }

                         #dtype_bool            { background-color: #FFB300; }
                         #dtype_hex             { background-color: #FFB300; }
                         #dtype_string          { background-color: #FF4444; }
                         #dtype_id              { background-color: #FF6644; }
                         #dtype_stream_id       { background-color: #FF6644; }
                         #dtype_raw             { background-color: #FF6644; }

                         #enum_custom           { background-color: #CC2222; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #CC2222; }
                        #dtype_real            { background-color: #FF6644; }
                        #dtype_float           { background-color: #FF6644; }
                        #dtype_int             { background-color: #FFB300; }

                        #dtype_complex_vector  { background-color: #AA1818; }
                        #dtype_real_vector     { background-color: #CC4433; }
                        #dtype_float_vector    { background-color: #CC4433; }
                        #dtype_int_vector      { background-color: #CC8800; }

                        #dtype_bool            { background-color: #FFB300; }
                        #dtype_hex             { background-color: #FFB300; }
                        #dtype_string          { background-color: #FF4444; }
                        #dtype_id              { background-color: #FF6644; }
                        #dtype_stream_id       { background-color: #FF6644; }
                        #dtype_raw             { background-color: #FF6644; }

                        #enum_custom           { background-color: #CC2222; }
                    """
