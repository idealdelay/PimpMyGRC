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
# fg colors — Arctic/Ice theme
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFFFFF')  # Bright white

BORDER_COLOR = get_color('#2A4A6A')     # Steel blue border

BORDER_COLOR_DISABLED = get_color('#2E4660')

FONT_COLOR = get_color('#AADDFF')       # Ice blue text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#2A1A2A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF4466')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#2A2A10')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#AAAA00')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#0C1428')  # Dark navy

COMMENT_BACKGROUND_COLOR = get_color('#0A0E18')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#0A1428')    # Dark navy blue

BLOCK_DISABLED_COLOR = get_color('#080F1F')

BLOCK_BYPASSED_COLOR = get_color('#1A1A10')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#66BBEE')  # Pale blue

CONNECTION_DISABLED_COLOR = get_color('#142434')

CONNECTION_ERROR_COLOR = get_color('#FF4444')


DEFAULT_DOMAIN_COLOR = get_color('#66BBEE')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — all blue shades for arctic look
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'snow'
AMBIENT_PARTICLE_COLOR = '#CCDDFF'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #4488CC; }
                         #dtype_real            { background-color: #88BBDD; }
                         #dtype_float           { background-color: #88BBDD; }
                         #dtype_int             { background-color: #AADDFF; }

                         #dtype_complex_vector  { background-color: #336699; }
                         #dtype_real_vector     { background-color: #6699AA; }
                         #dtype_float_vector    { background-color: #6699AA; }
                         #dtype_int_vector      { background-color: #88AACC; }

                         #dtype_bool            { background-color: #AADDFF; }
                         #dtype_hex             { background-color: #AADDFF; }
                         #dtype_string          { background-color: #CCDDEE; }
                         #dtype_id              { background-color: #AADDFF; }
                         #dtype_stream_id       { background-color: #AADDFF; }
                         #dtype_raw             { background-color: #AADDFF; }

                         #enum_custom           { background-color: #4488CC; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #4488CC; }
                        #dtype_real            { background-color: #88BBDD; }
                        #dtype_float           { background-color: #88BBDD; }
                        #dtype_int             { background-color: #AADDFF; }

                        #dtype_complex_vector  { background-color: #336699; }
                        #dtype_real_vector     { background-color: #6699AA; }
                        #dtype_float_vector    { background-color: #6699AA; }
                        #dtype_int_vector      { background-color: #88AACC; }

                        #dtype_bool            { background-color: #AADDFF; }
                        #dtype_hex             { background-color: #AADDFF; }
                        #dtype_string          { background-color: #CCDDEE; }
                        #dtype_id              { background-color: #AADDFF; }
                        #dtype_stream_id       { background-color: #AADDFF; }
                        #dtype_raw             { background-color: #AADDFF; }

                        #enum_custom           { background-color: #4488CC; }
                    """
