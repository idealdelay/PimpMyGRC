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
# Bubblegum — cotton candy pink & pastel fun
#################################################################################


# Font and border colors

HIGHLIGHT_COLOR = get_color('#FF69B4')  # Hot pink highlight

BORDER_COLOR = get_color('#E88FCF')     # Soft pink border

BORDER_COLOR_DISABLED = get_color('#9E7A8E')

FONT_COLOR = get_color('#FFE4F0')       # Pale pink-white text


# Missing blocks

MISSING_BLOCK_BACKGROUND_COLOR = get_color('#5E2040')
MISSING_BLOCK_BORDER_COLOR = get_color('#FF4488')


# Deprecated blocks

BLOCK_DEPRECATED_BACKGROUND_COLOR = get_color('#4A3A20')
BLOCK_DEPRECATED_BORDER_COLOR = get_color('#DDAA44')


# Flowgraph background

FLOWGRAPH_BACKGROUND_COLOR = get_color('#1E0E1A')  # Dark plum

COMMENT_BACKGROUND_COLOR = get_color('#2A1424')

FLOWGRAPH_EDGE_COLOR = COMMENT_BACKGROUND_COLOR


# Block color states

BLOCK_ENABLED_COLOR = get_color('#3A1A30')    # Dark berry

BLOCK_DISABLED_COLOR = get_color('#1A0E16')

BLOCK_BYPASSED_COLOR = get_color('#2A2A15')


# Connection colors

CONNECTION_ENABLED_COLOR = get_color('#FF88CC')  # Bubblegum pink

CONNECTION_DISABLED_COLOR = get_color('#3A1A2A')

CONNECTION_ERROR_COLOR = get_color('#FF2244')

DEFAULT_DOMAIN_COLOR = get_color('#FF88CC')
#################################################################################
# port colors
#################################################################################

PORT_TYPE_TO_COLOR = {key: get_color(
    color) for name, key, sizeof, color in Constants.CORE_TYPES}
PORT_TYPE_TO_COLOR.update((key, get_color(color))
                          for key, (_, color) in Constants.ALIAS_TYPES.items())


#################################################################################
# param box colors — candy pastels
#################################################################################

# Ambient particle effect
AMBIENT_PARTICLE_TYPE = 'bubbles'
AMBIENT_PARTICLE_COLOR = '#FF88CC'

DARK_THEME_STYLES = ".type_color_complex { color: #E066CC; } .type_color_float { color: #FF88AA; } .type_color_int { color: #88CCFF; } .type_color_short { color: #AADDFF; } .type_color_byte { color: #FFAA88; } .type_color_complex_vector { color: #CC55BB; } .type_color_float_vector { color: #DD7799; } .type_color_int_vector { color: #77BBEE; } .type_color_short_vector { color: #99CCEE; } .type_color_byte_vector { color: #EE9977; } .type_color_id { color: #FFB5D5; } .type_color_stream_id { color: #FFB5D5; } .type_color_bus_connection { color: #CC88DD; } .type_color_wildcard { color: #BBBBBB; } .type_color_message { color: #FFDD88; } .type_color_msg { color: #FFDD88; } .type_color_bus { color: #CC88DD; }"
LIGHT_THEME_STYLES = ".type_color_complex { color: #E066CC; } .type_color_float { color: #FF88AA; } .type_color_int { color: #88CCFF; } .type_color_short { color: #AADDFF; } .type_color_byte { color: #FFAA88; } .type_color_complex_vector { color: #CC55BB; } .type_color_float_vector { color: #DD7799; } .type_color_int_vector { color: #77BBEE; } .type_color_short_vector { color: #99CCEE; } .type_color_byte_vector { color: #EE9977; } .type_color_id { color: #FFB5D5; } .type_color_stream_id { color: #FFB5D5; } .type_color_bus_connection { color: #CC88DD; } .type_color_wildcard { color: #BBBBBB; } .type_color_message { color: #FFDD88; } .type_color_msg { color: #FFDD88; } .type_color_bus { color: #CC88DD; }"
