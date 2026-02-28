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
# fg colors — Phosphor Terminal theme
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFB300')  # Amber highlight

BORDER_COLOR = get_color('#1A3A1A')     # Dark green border

BORDER_COLOR_DISABLED = get_color('#355035')

FONT_COLOR = get_color('#33FF33')       # Phosphor green text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#3A1A0A')  # dark amber-red
MISSING_BLOCK_BORDER_COLOR = get_color('#FF4400')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#2A2A00')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#AAAA00')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#0A1A0A')  # Dark CRT green

COMMENT_BACKGROUND_COLOR = get_color('#0A0A0A')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#0A1F0A')    # Very dark green

BLOCK_DISABLED_COLOR = get_color('#0E160E')    # Dark muted green

BLOCK_BYPASSED_COLOR = get_color('#1A1A00')    # Dark amber


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#33FF33')  # Bright green

CONNECTION_DISABLED_COLOR = get_color('#143014')

CONNECTION_ERROR_COLOR = get_color('#FF3300')     # Red-orange error


DEFAULT_DOMAIN_COLOR = get_color('#33FF33')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — all green shades for phosphor look
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'matrix_rain'
AMBIENT_PARTICLE_COLOR = '#33FF33'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #00AA44; }
                         #dtype_real            { background-color: #33BB33; }
                         #dtype_float           { background-color: #33BB33; }
                         #dtype_int             { background-color: #44DD44; }

                         #dtype_complex_vector  { background-color: #008833; }
                         #dtype_real_vector     { background-color: #228822; }
                         #dtype_float_vector    { background-color: #228822; }
                         #dtype_int_vector      { background-color: #33AA33; }

                         #dtype_bool            { background-color: #44DD44; }
                         #dtype_hex             { background-color: #44DD44; }
                         #dtype_string          { background-color: #CCAA00; }
                         #dtype_id              { background-color: #33FF33; }
                         #dtype_stream_id       { background-color: #33FF33; }
                         #dtype_raw             { background-color: #33FF33; }

                         #enum_custom           { background-color: #228822; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #00AA44; }
                        #dtype_real            { background-color: #33BB33; }
                        #dtype_float           { background-color: #33BB33; }
                        #dtype_int             { background-color: #44DD44; }

                        #dtype_complex_vector  { background-color: #008833; }
                        #dtype_real_vector     { background-color: #228822; }
                        #dtype_float_vector    { background-color: #228822; }
                        #dtype_int_vector      { background-color: #33AA33; }

                        #dtype_bool            { background-color: #44DD44; }
                        #dtype_hex             { background-color: #44DD44; }
                        #dtype_string          { background-color: #CCAA00; }
                        #dtype_id              { background-color: #33FF33; }
                        #dtype_stream_id       { background-color: #33FF33; }
                        #dtype_raw             { background-color: #33FF33; }

                        #enum_custom           { background-color: #228822; }
                    """
