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
# fg colors — Military/Tactical theme
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFB300')  # Amber highlight

BORDER_COLOR = get_color('#3A4A2A')     # Olive border

BORDER_COLOR_DISABLED = get_color('#455638')

FONT_COLOR = get_color('#CCCC66')       # Amber-green text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#2A1A0A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF4400')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#2A2A00')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#AAAA00')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#141E0E')  # Dark olive drab

COMMENT_BACKGROUND_COLOR = get_color('#0E1210')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#1A2010')    # Dark olive

BLOCK_DISABLED_COLOR = get_color('#10170D')

BLOCK_BYPASSED_COLOR = get_color('#1A1A00')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#AAAA44')  # Olive-yellow

CONNECTION_DISABLED_COLOR = get_color('#161C0F')

CONNECTION_ERROR_COLOR = get_color('#FF4400')


DEFAULT_DOMAIN_COLOR = get_color('#AAAA44')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — olive/amber shades for military look
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'dust'
AMBIENT_PARTICLE_COLOR = '#998844'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #668833; }
                         #dtype_real            { background-color: #999944; }
                         #dtype_float           { background-color: #999944; }
                         #dtype_int             { background-color: #AAAA44; }

                         #dtype_complex_vector  { background-color: #556622; }
                         #dtype_real_vector     { background-color: #887733; }
                         #dtype_float_vector    { background-color: #887733; }
                         #dtype_int_vector      { background-color: #888833; }

                         #dtype_bool            { background-color: #AAAA44; }
                         #dtype_hex             { background-color: #AAAA44; }
                         #dtype_string          { background-color: #CCAA44; }
                         #dtype_id              { background-color: #CCCC66; }
                         #dtype_stream_id       { background-color: #CCCC66; }
                         #dtype_raw             { background-color: #CCCC66; }

                         #enum_custom           { background-color: #668833; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #668833; }
                        #dtype_real            { background-color: #999944; }
                        #dtype_float           { background-color: #999944; }
                        #dtype_int             { background-color: #AAAA44; }

                        #dtype_complex_vector  { background-color: #556622; }
                        #dtype_real_vector     { background-color: #887733; }
                        #dtype_float_vector    { background-color: #887733; }
                        #dtype_int_vector      { background-color: #888833; }

                        #dtype_bool            { background-color: #AAAA44; }
                        #dtype_hex             { background-color: #AAAA44; }
                        #dtype_string          { background-color: #CCAA44; }
                        #dtype_id              { background-color: #CCCC66; }
                        #dtype_stream_id       { background-color: #CCCC66; }
                        #dtype_raw             { background-color: #CCCC66; }

                        #enum_custom           { background-color: #668833; }
                    """
