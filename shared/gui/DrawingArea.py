"""
Copyright 2007, 2008, 2009, 2010 Free Software Foundation, Inc.
This file is part of GNU Radio

SPDX-License-Identifier: GPL-2.0-or-later

"""


import cairo
import time
from pathlib import Path

from gi.repository import Gtk, Gdk, GLib

from .canvas.colors import FLOWGRAPH_BACKGROUND_COLOR, HIGHLIGHT_COLOR
from . import Constants
from . import Actions

try:
    from . import effects
except ImportError:
    effects = None

try:
    from . import sounds
except ImportError:
    sounds = None

try:
    from .canvas.colors import AMBIENT_PARTICLE_TYPE, AMBIENT_PARTICLE_COLOR
except ImportError:
    AMBIENT_PARTICLE_TYPE = None
    AMBIENT_PARTICLE_COLOR = None

# User-level overrides — no sudo needed
_GNURADIO_DIR = Path.home() / ".gnuradio"
_BG_IMAGE_PATH = _GNURADIO_DIR / "grc_background.png"
_BG_COLOR_PATH = _GNURADIO_DIR / "grc_background_color"

_bg_surface = None
_bg_checked = False
_bg_color = None
_bg_color_checked = False


def _load_bg_color():
    """Load user background color override. Returns (r,g,b,a) tuple or None."""
    global _bg_color, _bg_color_checked
    if _bg_color_checked:
        return _bg_color
    _bg_color_checked = True
    if _BG_COLOR_PATH.is_file():
        try:
            h = _BG_COLOR_PATH.read_text().strip().lstrip('#')
            if len(h) == 6:
                _bg_color = (
                    int(h[0:2], 16) / 255.0,
                    int(h[2:4], 16) / 255.0,
                    int(h[4:6], 16) / 255.0,
                    1.0
                )
        except Exception:
            _bg_color = None
    return _bg_color


def _load_bg_surface():
    """Load the background image once. Returns cairo.ImageSurface or None."""
    global _bg_surface, _bg_checked
    if _bg_checked:
        return _bg_surface
    _bg_checked = True
    if _BG_IMAGE_PATH.is_file():
        try:
            _bg_surface = cairo.ImageSurface.create_from_png(str(_BG_IMAGE_PATH))
        except Exception:
            _bg_surface = None
    return _bg_surface


def reload_bg():
    """Force reload of background image and color (call after changing files)."""
    global _bg_surface, _bg_checked, _bg_color, _bg_color_checked
    _bg_surface = None
    _bg_checked = False
    _bg_color = None
    _bg_color_checked = False


def _fx_on(name):
    """Check if an effect is enabled (safe if effects module missing)."""
    if effects is None:
        return False
    if name == 'ambient_particles':
        return effects.get_ambient_mode() != 'off'
    return effects.is_enabled(name)


class DrawingArea(Gtk.DrawingArea):
    """
    DrawingArea is the gtk pixel map that graphical elements may draw themselves on.
    The drawing area also responds to mouse and key events.
    """

    def __init__(self, flow_graph):
        """
        DrawingArea constructor.
        Connect event handlers.

        Args:
            main_window: the main_window containing all flow graphs
        """
        Gtk.DrawingArea.__init__(self)

        self._flow_graph = flow_graph
        self.set_property('can_focus', True)

        self.zoom_factor = 1.0
        self._update_after_zoom = False
        self.ctrl_mask = False
        self.mod1_mask = False
        self.button_state = [False] * 10

        # Animation timer for continuous effects
        self._anim_timer_id = None

        # self.set_size_request(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.connect('realize', self._handle_window_realize)
        self.connect('draw', self.draw)
        self.connect('motion-notify-event', self._handle_mouse_motion)
        self.connect('button-press-event', self._handle_mouse_button_press)
        self.connect('button-release-event', self._handle_mouse_button_release)
        self.connect('scroll-event', self._handle_mouse_scroll)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.SCROLL_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |
            Gdk.EventMask.ENTER_NOTIFY_MASK
            # Gdk.EventMask.FOCUS_CHANGE_MASK
        )

        # This may not be the correct place to be handling the user events
        # Should this be in the page instead?
        # Or should more of the page functionality move here?

        # setup drag and drop
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.connect('drag-data-received', self._handle_drag_data_received)
        self.drag_dest_set_target_list(None)
        self.drag_dest_add_text_targets()

        # setup the focus flag
        self._focus_flag = False
        self.get_focus_flag = lambda: self._focus_flag

        def _handle_notify_event(widget, event, focus_flag):
            self._focus_flag = focus_flag

        self.connect('leave-notify-event', _handle_notify_event, False)
        self.connect('enter-notify-event', _handle_notify_event, True)

        self.set_can_focus(True)
        self.connect('focus-out-event', self._handle_focus_lost_event)

        self._ensure_anim_timer()

    ##########################################################################
    # Handlers
    ##########################################################################

    def _ensure_anim_timer(self):
        """Start the continuous animation timer if any animated effect is on."""
        if self._anim_timer_id is not None:
            return
        if not (_fx_on('ambient_particles') or _fx_on('data_flow_particles') or
                _fx_on('grid_overlay') or _fx_on('block_entrance_anim')):
            return

        def _anim_tick():
            self.queue_draw()
            return True  # keep running

        self._anim_timer_id = GLib.timeout_add(33, _anim_tick)  # ~30 fps

    def _handle_drag_data_received(self, widget, drag_context, x, y, selection_data, info, time):
        """
        Handle a drag and drop by adding a block at the given coordinate.
        """
        coords = x / self.zoom_factor, y / self.zoom_factor
        self._flow_graph.add_new_block(selection_data.get_text(), coords)

    def zoom_in(self):
        change = 1.2
        zoom_factor = min(self.zoom_factor * change, 5.0)
        self._set_zoom_factor(zoom_factor)

    def zoom_out(self):
        change = 1 / 1.2
        zoom_factor = max(self.zoom_factor * change, 0.1)
        self._set_zoom_factor(zoom_factor)

    def reset_zoom(self):
        self._set_zoom_factor(1.0)

    def _set_zoom_factor(self, zoom_factor):
        if zoom_factor != self.zoom_factor:
            self.zoom_factor = zoom_factor
            self._update_after_zoom = True
            self.queue_draw()

    def _handle_mouse_scroll(self, widget, event):
        if event.get_state() & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom_in()
            else:
                self.zoom_out()
            return True
        return False

    def _start_ripple_timer(self):
        """Start a short animation timer for click ripple effects."""
        if not _fx_on('click_ripple'):
            return
        if getattr(self, '_ripple_timer_id', None):
            return  # already running
        self._ripple_end = time.time() + 1.2  # ripple lasts ~1.2s

        def _tick():
            self.queue_draw()
            if time.time() > self._ripple_end:
                self._ripple_timer_id = None
                return False  # stop timer
            return True  # keep going

        self._ripple_timer_id = GLib.timeout_add(33, _tick)  # ~30 fps

    def _handle_mouse_button_press(self, widget, event):
        """
        Forward button click information to the flow graph.
        """
        self.grab_focus()

        self.ctrl_mask = event.get_state() & Gdk.ModifierType.CONTROL_MASK
        self.mod1_mask = event.get_state() & Gdk.ModifierType.MOD1_MASK
        self.button_state[event.button] = True

        if event.button == 1:
            double_click = (event.type == Gdk.EventType._2BUTTON_PRESS)
            self.button_state[1] = not double_click
            old_selected = set(self._flow_graph.selected_elements)
            self._flow_graph.handle_mouse_selector_press(
                double_click=double_click,
                coordinate=self._translate_event_coords(event),
            )
            self._start_ripple_timer()
            if sounds is not None and self._flow_graph.selected_elements - old_selected:
                sounds.play_click()
        elif event.button == 3:
            self._flow_graph.handle_mouse_context_press(
                coordinate=self._translate_event_coords(event),
                event=event,
            )

    def _handle_mouse_button_release(self, widget, event):
        """
        Forward button release information to the flow graph.
        """
        self.ctrl_mask = event.get_state() & Gdk.ModifierType.CONTROL_MASK
        self.mod1_mask = event.get_state() & Gdk.ModifierType.MOD1_MASK
        self.button_state[event.button] = False
        if event.button == 1:
            self._flow_graph.handle_mouse_selector_release(
                coordinate=self._translate_event_coords(event),
            )

    def _handle_mouse_motion(self, widget, event):
        """
        Forward mouse motion information to the flow graph.
        """
        self.ctrl_mask = event.get_state() & Gdk.ModifierType.CONTROL_MASK
        self.mod1_mask = event.get_state() & Gdk.ModifierType.MOD1_MASK

        if self.button_state[1]:
            self._auto_scroll(event)

        self._flow_graph.handle_mouse_motion(
            coordinate=self._translate_event_coords(event),
        )

    def _update_size(self):
        w, h = self._flow_graph.get_extents()[2:]
        self.set_size_request(
            w * self.zoom_factor + 100,
            h * self.zoom_factor + 100,
        )

    def _auto_scroll(self, event):
        x, y = event.x, event.y
        scrollbox = self.get_parent().get_parent()

        self._update_size()

        def scroll(pos, adj):
            """scroll if we moved near the border"""
            adj_val = adj.get_value()
            adj_len = adj.get_page_size()
            if pos - adj_val > adj_len - Constants.SCROLL_PROXIMITY_SENSITIVITY:
                adj.set_value(adj_val + Constants.SCROLL_DISTANCE)
                adj.emit('changed')
            elif pos - adj_val < Constants.SCROLL_PROXIMITY_SENSITIVITY:
                adj.set_value(adj_val - Constants.SCROLL_DISTANCE)
                adj.emit('changed')

        scroll(x, scrollbox.get_hadjustment())
        scroll(y, scrollbox.get_vadjustment())

    def _handle_window_realize(self, widget):
        """
        Called when the window is realized.
        Update the flowgraph, which calls new pixmap.
        """
        self._flow_graph.update()
        self._update_size()

    def _draw_grid_overlay(self, cr, width, height):
        """Draw a subtle themed grid on the canvas background."""
        spacing = 50
        cr.save()
        cr.set_source_rgba(HIGHLIGHT_COLOR[0], HIGHLIGHT_COLOR[1],
                           HIGHLIGHT_COLOR[2], 0.05)
        cr.set_line_width(0.5)
        x = 0
        while x <= width:
            cr.move_to(x, 0)
            cr.line_to(x, height)
            x += spacing
        y = 0
        while y <= height:
            cr.move_to(0, y)
            cr.line_to(width, y)
            y += spacing
        cr.stroke()
        cr.restore()

    def _draw_ambient_particles(self, cr, width, height):
        """Draw ambient particles on the canvas background."""
        if effects is None:
            return
        mode = effects.get_ambient_mode()
        if mode == 'off':
            return
        # Mode is the particle type directly (matrix_rain, bubbles, fire, etc.)
        ptype = mode
        pcolor = AMBIENT_PARTICLE_COLOR if AMBIENT_PARTICLE_COLOR else '#66CCFF'
        effects._ambient_particles.tick_and_draw(cr, width, height, ptype, pcolor)

    def draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        # Layer 1: Theme background color (always painted)
        cr.set_source_rgba(*FLOWGRAPH_BACKGROUND_COLOR)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Layer 2: User background image
        bg = _load_bg_surface()
        if bg is not None:
            bg_w = bg.get_width()
            bg_h = bg.get_height()
            if bg_w > 0 and bg_h > 0:
                cr.save()
                cr.scale(width / bg_w, height / bg_h)
                cr.set_source_surface(bg, 0, 0)
                cr.paint()
                cr.restore()

        # Layer 3: User background color override (on top of everything)
        bg_color = _load_bg_color()
        if bg_color is not None:
            cr.set_source_rgba(*bg_color)
            cr.rectangle(0, 0, width, height)
            cr.fill()

        # Layer 4: Grid overlay (before zoom, covers full canvas)
        if _fx_on('grid_overlay'):
            self._draw_grid_overlay(cr, width, height)

        # Layer 5: Ambient particles (before zoom, full canvas)
        if _fx_on('ambient_particles'):
            self._draw_ambient_particles(cr, width, height)

        cr.scale(self.zoom_factor, self.zoom_factor)
        cr.set_line_width(2.0 / self.zoom_factor)

        if self._update_after_zoom:
            self._flow_graph.create_labels(cr)
            self._flow_graph.create_shapes()
            self._update_size()
            self._update_after_zoom = False

        self._flow_graph.draw(cr)

    def _translate_event_coords(self, event):
        return event.x / self.zoom_factor, event.y / self.zoom_factor

    def _handle_focus_lost_event(self, widget, event):
        # don't clear selection while context menu is active
        if not self._flow_graph.get_context_menu()._menu.get_visible():
            self._flow_graph.unselect()
            self._flow_graph.update_selected()
            self.queue_draw()
            Actions.ELEMENT_SELECT()
