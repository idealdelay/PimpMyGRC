"""
GRC Visual Effects System — toggleable visual enhancements for themed GRC.

Provides:
  - Config loading/saving for ~/.gnuradio/grc_effects.json
  - AmbientParticleSystem (matrix_rain, snow, bubbles, confetti, sparks, dust)
  - DataFlowParticleManager (dots traveling along connections)
  - BlockEntranceTracker (fade-in animation for new blocks)
  - generate_toolbar_css() helper for GTK chrome theming
"""

import json
import math
import random
import time
from pathlib import Path

_GNURADIO_DIR = Path.home() / ".gnuradio"
_EFFECTS_PATH = _GNURADIO_DIR / "grc_effects.json"

# ─── Default config ──────────────────────────────────────────────────────────

_DEFAULTS = {
    "drop_shadows": True,
    "grid_overlay": False,
    "port_hover_glow": True,
    "data_flow_particles": False,
    "connection_gradient": True,
    "block_entrance_anim": True,
    "ambient_particles": False,
    "click_ripple": True,
    "toolbar_css": True,
}

_config = None


def _load():
    global _config
    if _config is not None:
        return
    _config = dict(_DEFAULTS)
    if _EFFECTS_PATH.is_file():
        try:
            with open(_EFFECTS_PATH) as f:
                user = json.load(f)
            if isinstance(user, dict):
                for k in _DEFAULTS:
                    if k in user and isinstance(user[k], bool):
                        _config[k] = user[k]
        except Exception:
            pass


def is_enabled(name):
    """Check whether a named effect is enabled."""
    _load()
    return _config.get(name, False)


def reload():
    """Force re-read of config from disk."""
    global _config
    _config = None
    _load()


def save(overrides=None):
    """Write current config (optionally merged with overrides) to disk."""
    _load()
    if overrides:
        _config.update(overrides)
    _GNURADIO_DIR.mkdir(parents=True, exist_ok=True)
    with open(_EFFECTS_PATH, "w") as f:
        json.dump(_config, f, indent=2)


def get_all():
    """Return a copy of the current config dict."""
    _load()
    return dict(_config)


# ─── Ambient Particle System ─────────────────────────────────────────────────

class _Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'alpha', 'life', 'char')


class AmbientParticleSystem:
    """Manages ambient background particles. Call tick_and_draw() each frame."""

    def __init__(self, max_particles=120):
        self._particles = []
        self._max = max_particles
        self._last_tick = 0

    def tick_and_draw(self, cr, w, h, ptype, color_hex):
        """Update and draw particles. ptype is one of:
        matrix_rain, snow, bubbles, confetti, sparks, dust"""
        now = time.time()
        dt = min(now - self._last_tick, 0.1) if self._last_tick else 0.033
        self._last_tick = now

        # Parse color
        hx = color_hex.lstrip('#')
        r = int(hx[0:2], 16) / 255.0
        g = int(hx[2:4], 16) / 255.0
        b = int(hx[4:6], 16) / 255.0

        # Spawn new particles
        spawn_rate = {
            'matrix_rain': 4, 'snow': 3, 'bubbles': 2,
            'confetti': 3, 'sparks': 4, 'dust': 2,
        }.get(ptype, 2)

        for _ in range(spawn_rate):
            if len(self._particles) >= self._max:
                break
            p = _Particle()
            p.life = 1.0
            if ptype == 'matrix_rain':
                p.x = random.uniform(0, w)
                p.y = -10
                p.vx = 0
                p.vy = random.uniform(150, 350)
                p.size = random.uniform(8, 14)
                p.alpha = random.uniform(0.3, 0.9)
                p.char = chr(random.randint(0x30A0, 0x30FF))
            elif ptype == 'snow':
                p.x = random.uniform(0, w)
                p.y = -5
                p.vx = random.uniform(-20, 20)
                p.vy = random.uniform(30, 80)
                p.size = random.uniform(2, 5)
                p.alpha = random.uniform(0.4, 0.8)
                p.char = None
            elif ptype == 'bubbles':
                p.x = random.uniform(0, w)
                p.y = h + 5
                p.vx = random.uniform(-10, 10)
                p.vy = random.uniform(-40, -80)
                p.size = random.uniform(3, 8)
                p.alpha = random.uniform(0.2, 0.5)
                p.char = None
            elif ptype == 'confetti':
                p.x = random.uniform(0, w)
                p.y = -5
                p.vx = random.uniform(-30, 30)
                p.vy = random.uniform(60, 140)
                p.size = random.uniform(3, 6)
                p.alpha = random.uniform(0.5, 0.9)
                p.char = None
            elif ptype == 'sparks':
                p.x = random.uniform(0, w)
                p.y = h + 2
                p.vx = random.uniform(-40, 40)
                p.vy = random.uniform(-120, -60)
                p.size = random.uniform(1.5, 3.5)
                p.alpha = random.uniform(0.6, 1.0)
                p.char = None
            else:  # dust
                p.x = random.uniform(0, w)
                p.y = random.uniform(0, h)
                p.vx = random.uniform(-8, 8)
                p.vy = random.uniform(-4, 4)
                p.size = random.uniform(1, 3)
                p.alpha = random.uniform(0.15, 0.35)
                p.char = None
            self._particles.append(p)

        # Update and draw
        alive = []
        for p in self._particles:
            p.x += p.vx * dt
            p.y += p.vy * dt

            # Confetti: add wobble
            if ptype == 'confetti':
                p.vx += random.uniform(-50, 50) * dt

            # Life decay
            if ptype == 'sparks':
                p.life -= dt * 1.2
            elif ptype == 'dust':
                p.life -= dt * 0.3
            else:
                p.life -= dt * 0.4

            if p.life <= 0 or p.y > h + 20 or p.y < -20 or p.x < -20 or p.x > w + 20:
                continue
            alive.append(p)

            alpha = p.alpha * min(p.life, 1.0)
            if alpha < 0.01:
                continue

            cr.save()
            if ptype == 'matrix_rain' and p.char:
                cr.set_source_rgba(r, g, b, alpha)
                cr.select_font_face("monospace", 0, 0)
                cr.set_font_size(p.size)
                cr.move_to(p.x, p.y)
                cr.show_text(p.char)
            elif ptype == 'bubbles':
                cr.arc(p.x, p.y, p.size, 0, 2 * math.pi)
                cr.set_source_rgba(r, g, b, alpha * 0.3)
                cr.fill_preserve()
                cr.set_source_rgba(r, g, b, alpha)
                cr.set_line_width(0.8)
                cr.stroke()
            elif ptype == 'confetti':
                # Small rotated rectangle
                cr.translate(p.x, p.y)
                cr.rotate(p.life * 6)
                cr.rectangle(-p.size / 2, -p.size / 2, p.size, p.size * 0.6)
                # Vary hue slightly per particle based on position
                rr = min(1, r + (p.x % 0.4) - 0.2)
                gg = min(1, g + (p.y % 0.3) - 0.15)
                cr.set_source_rgba(rr, gg, b, alpha)
                cr.fill()
            elif ptype == 'sparks':
                # Small bright dot with trail
                cr.arc(p.x, p.y, p.size, 0, 2 * math.pi)
                cr.set_source_rgba(r, g, b, alpha)
                cr.fill()
                # Tiny trail
                cr.move_to(p.x, p.y)
                cr.line_to(p.x - p.vx * dt * 2, p.y - p.vy * dt * 2)
                cr.set_source_rgba(r, g, b, alpha * 0.5)
                cr.set_line_width(p.size * 0.5)
                cr.stroke()
            else:  # snow, dust
                cr.arc(p.x, p.y, p.size, 0, 2 * math.pi)
                cr.set_source_rgba(r, g, b, alpha)
                cr.fill()
            cr.restore()

        self._particles = alive


# Module-level singleton
_ambient_particles = AmbientParticleSystem()


# ─── Data Flow Particle Manager ──────────────────────────────────────────────

class DataFlowParticleManager:
    """Manages dots traveling along connections."""

    def __init__(self):
        self._particles = {}  # conn_id -> list of {t, speed}
        self._last_tick = 0

    def tick(self):
        now = time.time()
        dt = min(now - self._last_tick, 0.1) if self._last_tick else 0.033
        self._last_tick = now

        for cid in list(self._particles.keys()):
            alive = []
            for dot in self._particles[cid]:
                dot['t'] += dot['speed'] * dt
                if dot['t'] < 1.0:
                    alive.append(dot)
            self._particles[cid] = alive

    def ensure_particles(self, conn_id):
        """Ensure a connection has flowing particles."""
        if conn_id not in self._particles:
            self._particles[conn_id] = []
        dots = self._particles[conn_id]
        if len(dots) < 3:
            dots.append({'t': 0.0, 'speed': random.uniform(0.3, 0.7)})

    def get_particles(self, conn_id):
        """Return list of t values (0..1) for dots on this connection."""
        return [d['t'] for d in self._particles.get(conn_id, [])]


_data_flow_particles = DataFlowParticleManager()


# ─── Block Entrance Tracker ──────────────────────────────────────────────────

class BlockEntranceTracker:
    """Tracks block creation times to provide fade-in alpha."""

    _DURATION = 0.35  # seconds

    def __init__(self):
        self._birth = {}  # block_id -> time

    def register(self, block_id):
        """Call when a block is first created/placed."""
        if block_id not in self._birth:
            self._birth[block_id] = time.time()

    def get_alpha(self, block_id):
        """Return alpha 0..1 for fade-in. Returns 1.0 if not tracked or done."""
        birth = self._birth.get(block_id)
        if birth is None:
            return 1.0
        elapsed = time.time() - birth
        if elapsed >= self._DURATION:
            del self._birth[block_id]
            return 1.0
        return elapsed / self._DURATION

    def has_active(self):
        """True if any block is still animating."""
        if not self._birth:
            return False
        now = time.time()
        self._birth = {k: v for k, v in self._birth.items()
                       if now - v < self._DURATION}
        return bool(self._birth)


_entrance_tracker = BlockEntranceTracker()


# ─── Toolbar CSS Generator ───────────────────────────────────────────────────

def generate_toolbar_css(bg, accent, text):
    """Generate CSS bytes for toolbar/menu theming.

    Args:
        bg: hex color string e.g. '#1A1A2E'
        accent: hex color string e.g. '#E94560'
        text: hex color string e.g. '#DDDDDD'

    Returns:
        bytes suitable for Gtk.CssProvider.load_from_data()
    """
    css = f"""
/* GRC theme toolbar styling */
headerbar, .titlebar {{
    background-color: {bg};
    color: {text};
    border-bottom: 1px solid {accent};
}}
menubar, menubar > menuitem {{
    background-color: {bg};
    color: {text};
}}
menubar > menuitem:hover {{
    background-color: {accent};
    color: {text};
}}
menu, .context-menu {{
    background-color: {bg};
    color: {text};
    border: 1px solid {accent};
}}
menu menuitem:hover {{
    background-color: {accent};
}}
toolbar, .toolbar {{
    background-color: {bg};
    color: {text};
    border-bottom: 1px solid {accent};
}}
toolbar button, .toolbar button {{
    color: {text};
    background-color: transparent;
}}
toolbar button:hover, .toolbar button:hover {{
    background-color: {accent};
}}
notebook header {{
    background-color: {bg};
}}
notebook header tab {{
    color: {text};
    background-color: {bg};
    border: 1px solid {accent};
}}
notebook header tab:checked {{
    background-color: {accent};
    color: {text};
}}
"""
    return css.encode('utf-8')
