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
# fg colors — Outrun / Synthwave theme
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFD700')  # Gold highlight

BORDER_COLOR = get_color('#6A2080')     # Purple border

BORDER_COLOR_DISABLED = get_color('#5A3A72')

FONT_COLOR = get_color('#FF6EC7')       # Hot pink text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#4A1A2A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF2266')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#3A2A10')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#CCAA00')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#1A0A2E')  # Deep purple canvas

COMMENT_BACKGROUND_COLOR = get_color('#1E0E32')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#2A1040')    # Dark purple

BLOCK_DISABLED_COLOR = get_color('#160B1F')

BLOCK_BYPASSED_COLOR = get_color('#2A2A10')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#00BFFF')  # Electric blue

CONNECTION_DISABLED_COLOR = get_color('#25173F')

CONNECTION_ERROR_COLOR = get_color('#FF0044')

DEFAULT_DOMAIN_COLOR = get_color('#00BFFF')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — pink/purple/blue shades for outrun look
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'confetti'
AMBIENT_PARTICLE_COLOR = '#FF00FF'

DARK_THEME_STYLES = b"""
                         #dtype_complex         { background-color: #8844CC; }
                         #dtype_real            { background-color: #FF6EC7; }
                         #dtype_float           { background-color: #FF6EC7; }
                         #dtype_int             { background-color: #00BFFF; }

                         #dtype_complex_vector  { background-color: #6633AA; }
                         #dtype_real_vector     { background-color: #CC5599; }
                         #dtype_float_vector    { background-color: #CC5599; }
                         #dtype_int_vector      { background-color: #0099CC; }

                         #dtype_bool            { background-color: #00BFFF; }
                         #dtype_hex             { background-color: #00BFFF; }
                         #dtype_string          { background-color: #FFD700; }
                         #dtype_id              { background-color: #FF6EC7; }
                         #dtype_stream_id       { background-color: #FF6EC7; }
                         #dtype_raw             { background-color: #FF6EC7; }

                         #enum_custom           { background-color: #8844CC; }
                     """
LIGHT_THEME_STYLES = b"""
                        #dtype_complex         { background-color: #8844CC; }
                        #dtype_real            { background-color: #FF6EC7; }
                        #dtype_float           { background-color: #FF6EC7; }
                        #dtype_int             { background-color: #00BFFF; }

                        #dtype_complex_vector  { background-color: #6633AA; }
                        #dtype_real_vector     { background-color: #CC5599; }
                        #dtype_float_vector    { background-color: #CC5599; }
                        #dtype_int_vector      { background-color: #0099CC; }

                        #dtype_bool            { background-color: #00BFFF; }
                        #dtype_hex             { background-color: #00BFFF; }
                        #dtype_string          { background-color: #FFD700; }
                        #dtype_id              { background-color: #FF6EC7; }
                        #dtype_stream_id       { background-color: #FF6EC7; }
                        #dtype_raw             { background-color: #FF6EC7; }

                        #enum_custom           { background-color: #8844CC; }
                    """
