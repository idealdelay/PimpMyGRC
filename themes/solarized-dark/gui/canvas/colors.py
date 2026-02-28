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
# fg colors — Solarized Dark theme
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#CB4B16')  # Solarized orange

BORDER_COLOR = get_color('#586E75')     # base01

BORDER_COLOR_DISABLED = get_color('#3A4D54')  # muted base1-ish

FONT_COLOR = get_color('#839496')       # base0 text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#3A1A1A')
MISSING_BLOCK_BORDER_COLOR = get_color('#DC322F')  # solarized red


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#2A2A00')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#B58900')  # solarized yellow


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#002B36')  # solarized base03

COMMENT_BACKGROUND_COLOR = get_color('#073642')  # base02

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#073642')    # base02

BLOCK_DISABLED_COLOR = get_color('#062129')   # softened blue-gray

BLOCK_BYPASSED_COLOR = get_color('#1A1A00')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#2AA198')  # solarized cyan

CONNECTION_DISABLED_COLOR = get_color('#06303A')

CONNECTION_ERROR_COLOR = get_color('#DC322F')     # solarized red


DEFAULT_DOMAIN_COLOR = get_color('#2AA198')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — solarized palette
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'dust'
AMBIENT_PARTICLE_COLOR = '#839496'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #268BD2; }
                         #dtype_real            { background-color: #CB4B16; }
                         #dtype_float           { background-color: #CB4B16; }
                         #dtype_int             { background-color: #2AA198; }

                         #dtype_complex_vector  { background-color: #1A6BA0; }
                         #dtype_real_vector     { background-color: #A0400E; }
                         #dtype_float_vector    { background-color: #A0400E; }
                         #dtype_int_vector      { background-color: #1A8A80; }

                         #dtype_bool            { background-color: #2AA198; }
                         #dtype_hex             { background-color: #2AA198; }
                         #dtype_string          { background-color: #D33682; }
                         #dtype_id              { background-color: #839496; }
                         #dtype_stream_id       { background-color: #839496; }
                         #dtype_raw             { background-color: #839496; }

                         #enum_custom           { background-color: #586E75; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #268BD2; }
                        #dtype_real            { background-color: #CB4B16; }
                        #dtype_float           { background-color: #CB4B16; }
                        #dtype_int             { background-color: #2AA198; }

                        #dtype_complex_vector  { background-color: #1A6BA0; }
                        #dtype_real_vector     { background-color: #A0400E; }
                        #dtype_float_vector    { background-color: #A0400E; }
                        #dtype_int_vector      { background-color: #1A8A80; }

                        #dtype_bool            { background-color: #2AA198; }
                        #dtype_hex             { background-color: #2AA198; }
                        #dtype_string          { background-color: #D33682; }
                        #dtype_id              { background-color: #839496; }
                        #dtype_stream_id       { background-color: #839496; }
                        #dtype_raw             { background-color: #839496; }

                        #enum_custom           { background-color: #586E75; }
                    """
