"""
Copyright 2007, 2008, 2009 Free Software Foundation, Inc.
This file is part of GNU Radio

SPDX-License-Identifier: GPL-2.0-or-later
"""

from argparse import Namespace
from math import pi
import time

from . import colors
from .drawable import Drawable
from .. import Utils
from ..Constants import (
    CONNECTOR_ARROW_BASE,
    CONNECTOR_ARROW_HEIGHT,
    GR_MESSAGE_DOMAIN,
    LINE_SELECT_SENSITIVITY,
)
import cairo as _cairo

try:
    from .. import effects
except ImportError:
    effects = None

from ...core.Connection import Connection as CoreConnection
from ...core.utils.descriptors import nop_write


class Connection(CoreConnection, Drawable):
    """
    A graphical connection for ports.
    The connection has 2 parts, the arrow and the wire.
    The coloring of the arrow and wire exposes the status of 3 states:
        enabled/disabled, valid/invalid, highlighted/non-highlighted.
    The wire coloring exposes the enabled and highlighted states.
    The arrow coloring exposes the enabled and valid states.
    """

    # ---- Outrun / Synthwave palette (RGBA) ----
    _NEON_WIRE = (0.00, 0.75, 1.00, 1.0)       # electric blue
    _NEON_ARROW = (1.00, 0.08, 0.58, 1.0)      # deep pink
    _NEON_HIGHLIGHT = (1.00, 0.84, 0.00, 1.0)  # gold
    _NEON_DISABLED = (0.23, 0.10, 0.29, 1.0)   # dim purple
    _NEON_ERROR = (1.00, 0.00, 0.27, 1.0)      # hot red
    # ------------------------------------------

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        Drawable.__init__(self)

        self._line = []
        self._line_width_factor = 1.0
        self._color1 = self._color2 = None

        self._current_port_rotations = self._current_coordinates = None

        self._rel_points = None  # connection coordinates relative to sink/source
        self._arrow_rotation = 0.0  # rotation of the arrow in radians
        self._current_cr = None  # for what_is_selected() of curved line
        self._line_path = None

    @nop_write
    @property
    def coordinate(self):
        return self.source_port.connector_coordinate_absolute

    @nop_write
    @property
    def rotation(self):
        """
        Get the 0 degree rotation.
        Rotations are irrelevant in connection.

        Returns:
            0
        """
        return 0

    def create_shapes(self):
        """Pre-calculate relative coordinates."""
        source = self.source_port
        sink = self.sink_port
        rotate = Utils.get_rotated_coordinate

        # first two components relative to source connector, rest relative to sink connector
        self._rel_points = [
            rotate((15, 0), source.rotation),
            rotate((50, 0), source.rotation),   # bezier curve control point 1
            rotate((-50, 0), sink.rotation),    # bezier curve control point 2
            rotate((-15, 0), sink.rotation),    # bezier curve end
            rotate((-CONNECTOR_ARROW_HEIGHT, 0), sink.rotation),  # line to arrow head
        ]
        self._current_coordinates = None  # triggers _make_path()

        def get_domain_color(domain_id):
            domain = self.parent_platform.domains.get(domain_id, None)
            return colors.get_color(domain.color) if domain else colors.DEFAULT_DOMAIN_COLOR

        if source.domain == GR_MESSAGE_DOMAIN:
            self._line_width_factor = 1.0
            self._color1 = None
            self._color2 = colors.CONNECTION_ENABLED_COLOR
        else:
            if source.domain != sink.domain:
                self._line_width_factor = 2.0
            self._color1 = get_domain_color(source.domain)
            self._color2 = get_domain_color(sink.domain)

        self._arrow_rotation = -sink.rotation / 180 * pi

        if not self._bounding_points:
            self._make_path()  # no cr set --> only sets bounding_points for extent

    def _make_path(self, cr=None):
        x_pos, y_pos = self.source_port.connector_coordinate_absolute
        x_end, y_end = self.sink_port.connector_coordinate_absolute

        x_e, y_e = x_end - x_pos, y_end - y_pos

        p0 = 0, 0
        p1, p2, (dx_e1, dy_e1), (dx_e2, dy_e2), (dx_e3, dy_e3) = self._rel_points
        p3 = x_e + dx_e1, y_e + dy_e1
        p4 = x_e + dx_e2, y_e + dy_e2
        p5 = x_e + dx_e3, y_e + dy_e3
        self._bounding_points = p0, p1, p4, p5  # ignores curved part =(

        if cr:
            cr.move_to(*p0)
            cr.line_to(*p1)
            cr.curve_to(*(p2 + p3 + p4))
            cr.line_to(*p5)
            self._line_path = cr.copy_path()

    @staticmethod
    def _is_too_dark(c):
        # Treat near-black as "invisible" on dark theme
        if not c:
            return True
        r, g, b, a = c
        return (r + g + b) < 0.35 or a < 0.2

    def draw(self, cr):
        """
        Draw the connection.
        """
        self._current_cr = cr
        sink = self.sink_port
        source = self.source_port

        port_rotations = (source.rotation, sink.rotation)
        if self._current_port_rotations != port_rotations:
            self.create_shapes()
            self._current_port_rotations = port_rotations

        new_coordinates = (source.parent_block.coordinate, sink.parent_block.coordinate)
        if self._current_coordinates != new_coordinates:
            self._make_path(cr)
            self._current_coordinates = new_coordinates

        # Apply the standard state logic first (highlight/disabled/error)
        def apply_state(base_color):
            if base_color is None:
                return None
            if self.highlighted:
                return self._NEON_HIGHLIGHT
            if not self.enabled:
                return self._NEON_DISABLED
            if not self.is_valid():
                return self._NEON_ERROR
            return base_color

        color1 = apply_state(self._color1)
        color2 = apply_state(self._color2)

        # Force hacker-vibe colors for enabled+valid+not-highlighted
        # so it NEVER ends up black even if domain colors are dark.
        if self.enabled and self.is_valid() and not self.highlighted:
            # Message connection: only color2 exists
            if source.domain == GR_MESSAGE_DOMAIN:
                color2 = self._NEON_ARROW
            else:
                # Stream connection: wire uses color1, arrow uses color2
                if self._is_too_dark(color1):
                    color1 = self._NEON_WIRE
                if self._is_too_dark(color2):
                    color2 = self._NEON_ARROW

        cr.translate(*self.coordinate)
        cr.set_line_width(self._line_width_factor * cr.get_line_width())
        cr.new_path()
        cr.append_path(self._line_path)

        arrow_pos = cr.get_current_point()

        # Glow pass makes it readable on dark backgrounds
        def glow(c):
            if not c:
                return
            r, g, b, a = c
            cr.save()
            cr.set_source_rgba(r, g, b, 0.22)
            cr.set_line_width(cr.get_line_width() * 3.2)
            cr.stroke_preserve()
            cr.restore()

        # Connection gradient effect
        _use_gradient = (effects and effects.is_enabled('connection_gradient') and
                         color1 and color2 and color1 != color2 and
                         self.enabled and self.is_valid() and not self.highlighted)

        if color1:  # not a message connection
            glow(color1)
            if _use_gradient:
                try:
                    x1, y1 = 0, 0
                    x2 = self.sink_port.connector_coordinate_absolute[0] - self.coordinate[0]
                    y2 = self.sink_port.connector_coordinate_absolute[1] - self.coordinate[1]
                    grad = _cairo.LinearGradient(x1, y1, x2, y2)
                    grad.add_color_stop_rgba(0, *color1)
                    grad.add_color_stop_rgba(1, *color2)
                    cr.set_source(grad)
                except Exception:
                    cr.set_source_rgba(*color1)
            else:
                cr.set_source_rgba(*color1)
            cr.stroke_preserve()

        if color1 != color2 and not _use_gradient:
            cr.save()
            cr.set_dash([5.0, 5.0], 5.0 if color1 else 0.0)
            glow(color2)
            cr.set_source_rgba(*color2)
            cr.stroke()
            cr.restore()
        else:
            cr.new_path()

        # Arrow head
        cr.save()
        cr.move_to(*arrow_pos)
        cr.set_source_rgba(*color2)
        cr.rotate(self._arrow_rotation)
        cr.rel_move_to(CONNECTOR_ARROW_HEIGHT, 0)
        cr.rel_line_to(-CONNECTOR_ARROW_HEIGHT, -CONNECTOR_ARROW_BASE / 2)
        cr.rel_line_to(0, CONNECTOR_ARROW_BASE)
        cr.close_path()
        cr.fill()
        cr.restore()

        # Marching ants on highlighted connections
        if self.highlighted and self._line_path:
            try:
                cr.save()
                cr.new_path()
                cr.append_path(self._line_path)
                offset = (time.time() * 60) % 24.0
                cr.set_dash([8.0, 8.0], offset)
                cr.set_line_width(3.0)
                cr.set_source_rgba(1.0, 0.84, 0.0, 0.85)
                cr.stroke()
                cr.restore()
            except Exception:
                cr.restore()

        # Data flow particles
        if (effects and effects.is_enabled('data_flow_particles') and
                self.enabled and self.is_valid() and self._line_path):
            try:
                conn_id = id(self)
                effects._data_flow_particles.ensure_particles(conn_id)
                effects._data_flow_particles.tick()
                for t in effects._data_flow_particles.get_particles(conn_id):
                    if 0 < t < 1:
                        cr.save()
                        cr.new_path()
                        cr.append_path(self._line_path)
                        # Walk the path to find position at parameter t
                        # Approximate: use source/sink coordinates
                        x1, y1 = 0, 0
                        x2 = self.sink_port.connector_coordinate_absolute[0] - self.coordinate[0]
                        y2 = self.sink_port.connector_coordinate_absolute[1] - self.coordinate[1]
                        px = x1 + (x2 - x1) * t
                        py = y1 + (y2 - y1) * t
                        cr.new_path()
                        cr.arc(px, py, 3.5, 0, 6.283)
                        c = color1 if color1 else color2
                        cr.set_source_rgba(c[0], c[1], c[2], 0.9)
                        cr.fill()
                        cr.restore()
            except Exception:
                pass

    def what_is_selected(self, coor, coor_m=None):
        """
        Returns:
            self if one of the areas/lines encompasses coor, else None.
        """
        if coor_m:
            return Drawable.what_is_selected(self, coor, coor_m)

        x, y = [a - b for a, b in zip(coor, self.coordinate)]
        cr = self._current_cr
        if cr is None:
            return

        cr.save()
        cr.new_path()
        cr.append_path(self._line_path)
        cr.set_line_width(cr.get_line_width() * LINE_SELECT_SENSITIVITY)
        hit = cr.in_stroke(x, y)
        cr.restore()

        if hit:
            return self


class DummyCoreConnection(object):
    def __init__(self, source_port, **kwargs):
        self.parent_platform = source_port.parent_platform
        self.source_port = source_port
        self.sink_port = self._dummy_port = Namespace(
            domain=source_port.domain,
            rotation=0,
            coordinate=(0, 0),
            connector_coordinate_absolute=(0, 0),
            connector_direction=0,
            parent_block=Namespace(coordinate=(0, 0)),
        )

        self.enabled = True
        self.highlighted = False
        self.is_valid = lambda: True
        self.update(**kwargs)

    def update(self, coordinate=None, rotation=None, sink_port=None):
        dp = self._dummy_port
        self.sink_port = sink_port if sink_port else dp
        if coordinate:
            dp.coordinate = coordinate
            dp.connector_coordinate_absolute = coordinate
            dp.parent_block.coordinate = coordinate
        if rotation is not None:
            dp.rotation = rotation
            dp.connector_direction = (180 + rotation) % 360

    @property
    def has_real_sink(self):
        return self.sink_port is not self._dummy_port


DummyConnection = Connection.make_cls_with_base(DummyCoreConnection)

