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
    # chars_per_color = 2 if len(color_code) > 4 else 1
    # offsets = range(1, 3 * chars_per_color + 1, chars_per_color)
    # return tuple(int(color_code[o:o + 2], 16) / 255.0 for o in offsets)

#################################################################################
# fg colors
#################################################################################



# Font and border colors

HIGHLIGHT_COLOR = get_color('#00FFFF')  # Cyan

BORDER_COLOR = get_color('#444444')

BORDER_COLOR_DISABLED = get_color('#666666')

FONT_COLOR = get_color('#DDDDDD')  # Light grey text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#4A2A2A')  # muted dark red

MISSING_BLOCK_BORDER_COLOR = get_color('#AA4444')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#554411')  # dark amber

BLOCK_DEPRECATED_BORDER_COLOR = get_color('#AA6600')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#142814')  # Dark green-tinted

COMMENT_BACKGROUND_COLOR = get_color('#2a2a2a')     # dark grey

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#2e2e5e')   # dark bluish

BLOCK_DISABLED_COLOR = get_color('#171717')

BLOCK_BYPASSED_COLOR = get_color('#4f4f2f')  # muted yellow-green


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#AAAAAA')

CONNECTION_DISABLED_COLOR = get_color('#444444')

CONNECTION_ERROR_COLOR = get_color('#FF4444')


DEFAULT_DOMAIN_COLOR = get_color('#888888')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'matrix_rain'
AMBIENT_PARTICLE_COLOR = '#00FF66'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #3399FF; }
                         #dtype_real            { background-color: #FF8C69; }
                         #dtype_float           { background-color: #FF8C69; }
                         #dtype_int             { background-color: #00FF99; }

                         #dtype_complex_vector  { background-color: #3399AA; }
                         #dtype_real_vector     { background-color: #CC8C69; }
                         #dtype_float_vector    { background-color: #CC8C69; }
                         #dtype_int_vector      { background-color: #00CC99; }

                         #dtype_bool            { background-color: #00FF99; }
                         #dtype_hex             { background-color: #00FF99; }
                         #dtype_string          { background-color: #CC66CC; }
                         #dtype_id              { background-color: #DDDDDD; }
                         #dtype_stream_id       { background-color: #DDDDDD; }
                         #dtype_raw             { background-color: #DDDDDD; }

                         #enum_custom           { background-color: #EEEEEE; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #3399FF; }
                        #dtype_real            { background-color: #FF8C69; }
                        #dtype_float           { background-color: #FF8C69; }
                        #dtype_int             { background-color: #00FF99; }

                        #dtype_complex_vector  { background-color: #3399AA; }
                        #dtype_real_vector     { background-color: #CC8C69; }
                        #dtype_float_vector    { background-color: #CC8C69; }
                        #dtype_int_vector      { background-color: #00CC99; }

                        #dtype_bool            { background-color: #00FF99; }
                        #dtype_hex             { background-color: #00FF99; }
                        #dtype_string          { background-color: #CC66CC; }
                        #dtype_id              { background-color: #DDDDDD; }
                        #dtype_stream_id       { background-color: #DDDDDD; }
                        #dtype_raw             { background-color: #FFFFFF; }

                        #enum_custom           { background-color: #EEEEEE; }
                    """
