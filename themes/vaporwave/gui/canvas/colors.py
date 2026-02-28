"""
Copyright 2008,2013 Free Software Foundation, Inc.
This file is part of GNU Radio

SPDX-License-Identifier: GPL-2.0-or-later

"""


from gi.repository import Gtk, Gdk, cairo

from .. import Constants


def get_color(color_code):
    color = Gdk.RGBA()
    color.parse(color_code)
    return color.red, color.green, color.blue, color.alpha

#################################################################################
# Vaporwave — aesthetic pastel purple/pink/teal
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#00FFCC')  # Teal/cyan highlight

BORDER_COLOR = get_color('#AA66CC')     # Soft purple border

BORDER_COLOR_DISABLED = get_color('#665577')

FONT_COLOR = get_color('#E0D0FF')       # Lavender text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#3A1A3A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF44AA')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#2A2A15')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#CCAA44')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#160E20')  # Deep purple-black

COMMENT_BACKGROUND_COLOR = get_color('#1E1428')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#261440')    # Purple haze

BLOCK_DISABLED_COLOR = get_color('#120A1E')

BLOCK_BYPASSED_COLOR = get_color('#22221A')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#66FFCC')  # Mint/teal

CONNECTION_DISABLED_COLOR = get_color('#221433')

CONNECTION_ERROR_COLOR = get_color('#FF3388')

DEFAULT_DOMAIN_COLOR = get_color('#66FFCC')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — aesthetic pastels: lavender, pink, teal, peach
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'confetti'
AMBIENT_PARTICLE_COLOR = '#CC88FF'

DARK_THEME_STYLES = ".type_color_complex { color: #BB77DD; } .type_color_float { color: #FF77AA; } .type_color_int { color: #55DDCC; } .type_color_short { color: #77EEDD; } .type_color_byte { color: #FFAA77; } .type_color_complex_vector { color: #9955BB; } .type_color_float_vector { color: #DD5588; } .type_color_int_vector { color: #44BBAA; } .type_color_short_vector { color: #66CCBB; } .type_color_byte_vector { color: #DD8855; } .type_color_id { color: #E0AAFF; } .type_color_stream_id { color: #E0AAFF; } .type_color_bus_connection { color: #FF88CC; } .type_color_wildcard { color: #BBAACC; } .type_color_message { color: #88FFDD; } .type_color_msg { color: #88FFDD; } .type_color_bus { color: #FF88CC; }"
LIGHT_THEME_STYLES = ".type_color_complex { color: #BB77DD; } .type_color_float { color: #FF77AA; } .type_color_int { color: #55DDCC; } .type_color_short { color: #77EEDD; } .type_color_byte { color: #FFAA77; } .type_color_complex_vector { color: #9955BB; } .type_color_float_vector { color: #DD5588; } .type_color_int_vector { color: #44BBAA; } .type_color_short_vector { color: #66CCBB; } .type_color_byte_vector { color: #DD8855; } .type_color_id { color: #E0AAFF; } .type_color_stream_id { color: #E0AAFF; } .type_color_bus_connection { color: #FF88CC; } .type_color_wildcard { color: #BBAACC; } .type_color_message { color: #88FFDD; } .type_color_msg { color: #88FFDD; } .type_color_bus { color: #FF88CC; }"
