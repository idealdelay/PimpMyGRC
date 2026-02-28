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
# Amber Terminal — classic amber phosphor on black
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FFCC00')  # Bright amber highlight

BORDER_COLOR = get_color('#CC8800')     # Warm amber border

BORDER_COLOR_DISABLED = get_color('#665522')

FONT_COLOR = get_color('#FFBB33')       # Amber text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#3A1A0A')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF4400')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#332200')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#AA7700')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#0E0A04')  # Near-black warm

COMMENT_BACKGROUND_COLOR = get_color('#141008')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#1A1408')    # Dark amber-brown

BLOCK_DISABLED_COLOR = get_color('#0E0A06')

BLOCK_BYPASSED_COLOR = get_color('#1A1A0A')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#FFAA00')  # Bright amber

CONNECTION_DISABLED_COLOR = get_color('#2A1A0A')

CONNECTION_ERROR_COLOR = get_color('#FF3300')

DEFAULT_DOMAIN_COLOR = get_color('#FFAA00')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — shades of amber/gold/brown
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'sparks'
AMBIENT_PARTICLE_COLOR = '#FFB300'

DARK_THEME_STYLES = ".type_color_complex { color: #DDAA22; } .type_color_float { color: #FFBB33; } .type_color_int { color: #CC8800; } .type_color_short { color: #DD9922; } .type_color_byte { color: #AA7711; } .type_color_complex_vector { color: #BB8811; } .type_color_float_vector { color: #DD9922; } .type_color_int_vector { color: #AA6600; } .type_color_short_vector { color: #BB7711; } .type_color_byte_vector { color: #886600; } .type_color_id { color: #FFCC44; } .type_color_stream_id { color: #FFCC44; } .type_color_bus_connection { color: #DDAA33; } .type_color_wildcard { color: #998866; } .type_color_message { color: #FFD700; } .type_color_msg { color: #FFD700; } .type_color_bus { color: #DDAA33; }"
LIGHT_THEME_STYLES = ".type_color_complex { color: #DDAA22; } .type_color_float { color: #FFBB33; } .type_color_int { color: #CC8800; } .type_color_short { color: #DD9922; } .type_color_byte { color: #AA7711; } .type_color_complex_vector { color: #BB8811; } .type_color_float_vector { color: #DD9922; } .type_color_int_vector { color: #AA6600; } .type_color_short_vector { color: #BB7711; } .type_color_byte_vector { color: #886600; } .type_color_id { color: #FFCC44; } .type_color_stream_id { color: #FFCC44; } .type_color_bus_connection { color: #DDAA33; } .type_color_wildcard { color: #998866; } .type_color_message { color: #FFD700; } .type_color_msg { color: #FFD700; } .type_color_bus { color: #DDAA33; }"
