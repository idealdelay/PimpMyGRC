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
# Circus — bold primaries, big top energy
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFD700')  # Gold spotlight

BORDER_COLOR = get_color('#DD3333')     # Red tent border

BORDER_COLOR_DISABLED = get_color('#885544')

FONT_COLOR = get_color('#FFFFDD')       # Warm cream text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#4A1A1A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF3333')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#443311')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#CC8800')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#140A08')  # Dark tent interior

COMMENT_BACKGROUND_COLOR = get_color('#1E1410')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#2A1810')    # Dark warm brown

BLOCK_DISABLED_COLOR = get_color('#140E0A')

BLOCK_BYPASSED_COLOR = get_color('#2A2A10')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#FFCC00')  # Bright yellow

CONNECTION_DISABLED_COLOR = get_color('#3A2A1A')

CONNECTION_ERROR_COLOR = get_color('#FF0033')

DEFAULT_DOMAIN_COLOR = get_color('#FFCC00')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — circus primaries: red, blue, yellow, green
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'confetti'
AMBIENT_PARTICLE_COLOR = '#FFDD00'

DARK_THEME_STYLES = ".type_color_complex { color: #DD2222; } .type_color_float { color: #FF8800; } .type_color_int { color: #2288FF; } .type_color_short { color: #44AAFF; } .type_color_byte { color: #22CC44; } .type_color_complex_vector { color: #BB1111; } .type_color_float_vector { color: #DD6600; } .type_color_int_vector { color: #1166DD; } .type_color_short_vector { color: #3399DD; } .type_color_byte_vector { color: #11AA33; } .type_color_id { color: #FFDD00; } .type_color_stream_id { color: #FFDD00; } .type_color_bus_connection { color: #DD22DD; } .type_color_wildcard { color: #CCCCCC; } .type_color_message { color: #FFD700; } .type_color_msg { color: #FFD700; } .type_color_bus { color: #DD22DD; }"
LIGHT_THEME_STYLES = ".type_color_complex { color: #DD2222; } .type_color_float { color: #FF8800; } .type_color_int { color: #2288FF; } .type_color_short { color: #44AAFF; } .type_color_byte { color: #22CC44; } .type_color_complex_vector { color: #BB1111; } .type_color_float_vector { color: #DD6600; } .type_color_int_vector { color: #1166DD; } .type_color_short_vector { color: #3399DD; } .type_color_byte_vector { color: #11AA33; } .type_color_id { color: #FFDD00; } .type_color_stream_id { color: #FFDD00; } .type_color_bus_connection { color: #DD22DD; } .type_color_wildcard { color: #CCCCCC; } .type_color_message { color: #FFD700; } .type_color_msg { color: #FFD700; } .type_color_bus { color: #DD22DD; }"
