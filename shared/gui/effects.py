"""
PimpMyGRC Visual Effects — toggleable visual enhancements for themed GRC.

Provides:
  - Config loading/saving for ~/.gnuradio/grc_effects.json
  - AmbientParticleSystem (matrix_rain, snow, bubbles, confetti, sparks, dust)
  - DataFlowParticleManager (dots traveling along connections)
  - BlockEntranceTracker (fade-in animation for new blocks)
  - generate_toolbar_css() helper for GTK chrome theming
"""

import cairo
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
    "ambient_particles": "off",    # "off", "bubbles", or "fire"
    "click_sound": "off",           # "off", "sonar", "click", "coin", "laser", "blip"
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
                    if k not in user:
                        continue
                    default_val = _DEFAULTS[k]
                    user_val = user[k]
                    if isinstance(default_val, bool) and isinstance(user_val, bool):
                        _config[k] = user_val
                    elif isinstance(default_val, str) and isinstance(user_val, str):
                        _config[k] = user_val
                    # Backward compat: old bool True -> "bubbles"
                    elif k == 'ambient_particles' and user_val is True:
                        _config[k] = "bubbles"
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


_VALID_SOUNDS = ('off', 'sonar', 'click', 'coin', 'laser', 'blip')

_VALID_AMBIENT = ('off', 'matrix_rain', 'bubbles', 'snow',
                   'confetti', 'sparks', 'dust', 'fire',
                   'fireflies', 'lightning', 'starfield',
                   'scanline', 'glitch')

def get_ambient_mode():
    """Return the ambient particle mode/type string."""
    _load()
    val = _config.get('ambient_particles', 'off')
    if val in _VALID_AMBIENT:
        return val
    if val is True:
        return 'bubbles'
    return 'off'


def get_click_sound():
    """Return the click sound type string."""
    _load()
    val = _config.get('click_sound', 'off')
    if val in _VALID_SOUNDS:
        return val
    return 'off'


def get_all():
    """Return a copy of the current config dict."""
    _load()
    return dict(_config)


# ─── Ambient Particle System ─────────────────────────────────────────────────

class _Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'alpha', 'life', 'char',
                 'seed', 'max_life', 'x2', 'y2', 'angle', 'segments')


class AmbientParticleSystem:
    """Manages ambient background particles. Call tick_and_draw() each frame."""

    def __init__(self, max_particles=120):
        self._particles = []
        self._max = max_particles
        self._last_tick = 0
        self._time = 0

    def tick_and_draw(self, cr, w, h, ptype, color_hex):
        """Update and draw particles. ptype is one of:
        matrix_rain, snow, bubbles, confetti, sparks, dust"""
        now = time.time()
        dt = min(now - self._last_tick, 0.1) if self._last_tick else 0.033
        self._last_tick = now
        self._time += dt

        # Parse color
        hx = color_hex.lstrip('#')
        r = int(hx[0:2], 16) / 255.0
        g = int(hx[2:4], 16) / 255.0
        b = int(hx[4:6], 16) / 255.0

        # Particle budget per type
        if ptype == 'fire':
            cap = 250
        elif ptype == 'matrix_rain':
            cap = 200
        elif ptype == 'starfield':
            cap = 180
        elif ptype == 'lightning':
            cap = 8
        elif ptype == 'scanline':
            cap = 3
        elif ptype == 'glitch':
            cap = 15
        else:
            cap = self._max

        # Spawn new particles
        spawn_rate = {
            'matrix_rain': 4, 'snow': 3, 'bubbles': 2,
            'confetti': 3, 'sparks': 4, 'dust': 2, 'fire': 6,
            'fireflies': 1, 'lightning': 1, 'starfield': 5,
            'scanline': 1, 'glitch': 2,
        }.get(ptype, 2)

        for _ in range(spawn_rate):
            if len(self._particles) >= cap:
                break
            p = _Particle()
            p.life = 1.0
            p.seed = 0
            p.max_life = 1.0
            if ptype == 'matrix_rain':
                p.x = random.uniform(0, w)
                p.y = random.uniform(-20, -5)
                p.vx = 0
                p.vy = random.uniform(120, 300)
                p.size = random.uniform(16, 28)
                p.alpha = random.uniform(0.3, 0.9)
                p.life = 99.0   # killed by going off-screen, not life
                p.max_life = 99.0
                p.char = random.choice('01')
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
            elif ptype == 'fire':
                # Mix of flame body + embers for realism
                is_ember = random.random() < 0.12
                if is_ember:
                    # Tiny bright ember that rises high
                    p.x = random.gauss(w * 0.5, w * 0.25)
                    p.y = h + random.uniform(-5, 5)
                    p.vx = random.uniform(-15, 15)
                    p.vy = random.uniform(-140, -60)
                    p.size = random.uniform(1.0, 2.5)
                    p.alpha = random.uniform(0.7, 1.0)
                    p.char = 'e'  # ember
                    p.life = random.uniform(1.5, 3.0)
                else:
                    # Main flame body — clustered at bottom
                    p.x = random.gauss(w * 0.5, w * 0.22)
                    p.y = h + random.uniform(-2, 8)
                    p.vx = random.uniform(-5, 5)
                    p.vy = random.uniform(-80, -20)
                    p.size = random.uniform(14, 40)
                    p.alpha = random.uniform(0.3, 0.7)
                    p.char = 'f'  # flame
                    p.life = random.uniform(1.2, 2.5)
                p.seed = random.uniform(0, 100)
                p.max_life = p.life
            elif ptype == 'fireflies':
                p.x = random.uniform(0, w)
                p.y = random.uniform(0, h)
                p.vx = random.uniform(-15, 15)
                p.vy = random.uniform(-15, 15)
                p.size = random.uniform(2, 5)
                p.alpha = random.uniform(0.1, 0.8)
                p.life = random.uniform(3.0, 8.0)
                p.max_life = p.life
                p.seed = random.uniform(0, 100)
                p.char = None
            elif ptype == 'lightning':
                # A bolt: start at top, zig-zag down
                p.x = random.uniform(w * 0.1, w * 0.9)
                p.y = 0
                p.x2 = p.x + random.uniform(-80, 80)
                p.y2 = random.uniform(h * 0.4, h)
                p.vx = 0
                p.vy = 0
                p.size = random.uniform(1.5, 3.0)
                p.alpha = random.uniform(0.7, 1.0)
                p.life = random.uniform(0.15, 0.35)
                p.max_life = p.life
                p.seed = random.random()
                p.char = 'L'
                # Pre-generate zigzag segments
                segs = [(p.x, p.y)]
                cx, cy = p.x, p.y
                steps = random.randint(5, 12)
                for si in range(steps):
                    t = (si + 1) / steps
                    tx = p.x + (p.x2 - p.x) * t
                    ty = p.y + (p.y2 - p.y) * t
                    cx = tx + random.uniform(-30, 30)
                    cy = ty
                    segs.append((cx, cy))
                p.segments = segs
            elif ptype == 'starfield':
                # Stars radiate outward from center
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(5, 30)
                cx, cy = w / 2, h / 2
                p.x = cx + math.cos(angle) * dist
                p.y = cy + math.sin(angle) * dist
                speed = random.uniform(150, 400)
                p.vx = math.cos(angle) * speed
                p.vy = math.sin(angle) * speed
                p.size = random.uniform(1, 2.5)
                p.alpha = random.uniform(0.3, 0.9)
                p.life = 99.0  # dies off-screen
                p.max_life = 99.0
                p.char = None
                p.angle = angle
            elif ptype == 'scanline':
                p.x = 0
                p.y = -2
                p.vx = 0
                p.vy = random.uniform(80, 160)
                p.size = random.uniform(1, 3)
                p.alpha = random.uniform(0.3, 0.6)
                p.life = 99.0  # dies off-screen
                p.max_life = 99.0
                p.char = 'S'
            elif ptype == 'glitch':
                p.x = random.uniform(0, w - 60)
                p.y = random.uniform(0, h - 10)
                p.vx = random.uniform(30, 100)  # width
                p.vy = random.uniform(3, 12)     # height
                p.size = 0
                p.alpha = random.uniform(0.15, 0.5)
                p.life = random.uniform(0.05, 0.2)
                p.max_life = p.life
                p.seed = random.random()
                p.char = 'G'
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

            # Life decay (matrix_rain/starfield/scanline die off-screen only)
            if ptype in ('matrix_rain', 'starfield', 'scanline'):
                pass
            elif ptype == 'sparks':
                p.life -= dt * 1.2
            elif ptype == 'fire':
                p.life -= dt
                # Sinusoidal licking motion — each particle has unique phase
                t_wave = self._time * 1.8 + getattr(p, 'seed', 0)
                if getattr(p, 'char', '') == 'f':
                    p.vx += math.sin(t_wave) * 40 * dt
                    p.vy -= random.uniform(5, 20) * dt
                    p.vx *= (1.0 - 1.5 * dt)
                else:
                    p.vx += math.sin(t_wave * 1.2) * 15 * dt
                    p.vy -= random.uniform(0, 10) * dt
            elif ptype == 'fireflies':
                p.life -= dt * 0.2
                # Wander randomly
                p.vx += random.uniform(-30, 30) * dt
                p.vy += random.uniform(-30, 30) * dt
                p.vx *= 0.95
                p.vy *= 0.95
                # Pulsing glow via alpha
                seed = getattr(p, 'seed', 0)
                p.alpha = 0.15 + 0.65 * (0.5 + 0.5 * math.sin(
                    self._time * 3.0 + seed))
            elif ptype in ('lightning', 'glitch'):
                p.life -= dt
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
            elif ptype == 'fire':
                ml = getattr(p, 'max_life', 1.0) or 1.0
                age = 1.0 - (p.life / ml)  # 0 = just born, 1 = dying
                age = max(0.0, min(1.0, age))

                if getattr(p, 'char', '') == 'e':
                    # ── Ember: tiny bright dot with short trail ──
                    # Color: bright yellow → orange → red
                    if age < 0.4:
                        fr, fg, fb = 1.0, 0.85, 0.3
                    elif age < 0.7:
                        t2 = (age - 0.4) / 0.3
                        fr, fg, fb = 1.0, 0.85 - t2 * 0.5, 0.3 - t2 * 0.3
                    else:
                        t2 = (age - 0.7) / 0.3
                        fr, fg, fb = 1.0 - t2 * 0.4, 0.35 - t2 * 0.25, 0.0
                    ea = alpha * (1.0 - age * 0.7)
                    cr.arc(p.x, p.y, p.size, 0, 2 * math.pi)
                    cr.set_source_rgba(fr, fg, fb, ea)
                    cr.fill()
                    # Glow halo
                    cr.arc(p.x, p.y, p.size * 3, 0, 2 * math.pi)
                    cr.set_source_rgba(fr, fg * 0.5, 0, ea * 0.15)
                    cr.fill()
                else:
                    # ── Flame body: soft teardrop with color ramp ──
                    # Smooth color: white-yellow → orange → red → dark
                    if age < 0.15:
                        fr, fg, fb = 1.0, 0.97, 0.7
                    elif age < 0.35:
                        t2 = (age - 0.15) / 0.2
                        fr = 1.0
                        fg = 0.97 - t2 * 0.42   # → 0.55
                        fb = 0.7 - t2 * 0.7      # → 0.0
                    elif age < 0.6:
                        t2 = (age - 0.35) / 0.25
                        fr = 1.0 - t2 * 0.15     # → 0.85
                        fg = 0.55 - t2 * 0.35    # → 0.2
                        fb = 0.0
                    elif age < 0.85:
                        t2 = (age - 0.6) / 0.25
                        fr = 0.85 - t2 * 0.35    # → 0.5
                        fg = 0.2 - t2 * 0.15     # → 0.05
                        fb = 0.0
                    else:
                        t2 = (age - 0.85) / 0.15
                        fr = 0.5 - t2 * 0.3
                        fg = 0.05 - t2 * 0.05
                        fb = 0.0

                    # Size shrinks as flame rises, stretch makes it taller
                    sz = p.size * (0.35 + 0.65 * (1.0 - age))
                    stretch = 1.4 + 1.0 * (1.0 - age)
                    fa = alpha * (1.0 - age ** 2)

                    # Outer glow (large, very soft)
                    cr.save()
                    cr.translate(p.x, p.y)
                    cr.scale(1.0, stretch)
                    pat = cairo.RadialGradient(0, -sz * 0.15, 0,
                                               0, 0, sz * 1.3)
                    pat.add_color_stop_rgba(0.0, fr, fg, fb, fa * 0.35)
                    pat.add_color_stop_rgba(0.6, fr * 0.8, fg * 0.4, 0, fa * 0.12)
                    pat.add_color_stop_rgba(1.0, 0.2, 0, 0, 0)
                    cr.set_source(pat)
                    cr.arc(0, 0, sz * 1.3, 0, 2 * math.pi)
                    cr.fill()
                    cr.restore()

                    # Core flame (bright center offset upward)
                    cr.save()
                    cr.translate(p.x, p.y)
                    cr.scale(1.0, stretch)
                    pat = cairo.RadialGradient(0, -sz * 0.25, sz * 0.08,
                                               0, sz * 0.05, sz * 0.85)
                    core_a = min(1.0, fa * 1.2)
                    pat.add_color_stop_rgba(0.0, min(1, fr + 0.1),
                                            min(1, fg + 0.1),
                                            min(1, fb + 0.15), core_a)
                    pat.add_color_stop_rgba(0.4, fr, fg * 0.6, 0, fa * 0.6)
                    pat.add_color_stop_rgba(1.0, fr * 0.3, 0, 0, 0)
                    cr.set_source(pat)
                    cr.arc(0, 0, sz * 0.85, 0, 2 * math.pi)
                    cr.fill()
                    cr.restore()
            elif ptype == 'fireflies':
                # Glowing dot with halo
                cr.arc(p.x, p.y, p.size * 2.5, 0, 2 * math.pi)
                cr.set_source_rgba(r, g, b, alpha * 0.15)
                cr.fill()
                cr.arc(p.x, p.y, p.size, 0, 2 * math.pi)
                cr.set_source_rgba(r, g, b, alpha)
                cr.fill()
            elif ptype == 'lightning':
                segs = getattr(p, 'segments', None)
                if segs and len(segs) > 1:
                    # Bright bolt
                    cr.set_line_width(p.size)
                    cr.set_source_rgba(r, g, b, alpha)
                    cr.move_to(segs[0][0], segs[0][1])
                    for sx, sy in segs[1:]:
                        cr.line_to(sx, sy)
                    cr.stroke()
                    # White-hot core
                    cr.set_line_width(max(0.5, p.size * 0.4))
                    cr.set_source_rgba(1, 1, 1, alpha * 0.7)
                    cr.move_to(segs[0][0], segs[0][1])
                    for sx, sy in segs[1:]:
                        cr.line_to(sx, sy)
                    cr.stroke()
                    # Glow around bolt
                    cr.set_line_width(p.size * 4)
                    cr.set_source_rgba(r, g, b, alpha * 0.08)
                    cr.move_to(segs[0][0], segs[0][1])
                    for sx, sy in segs[1:]:
                        cr.line_to(sx, sy)
                    cr.stroke()
            elif ptype == 'starfield':
                # Streak that gets longer as it moves outward
                dist = math.sqrt((p.x - w / 2) ** 2 + (p.y - h / 2) ** 2)
                streak = min(dist * 0.06, 15)
                a = getattr(p, 'angle', 0)
                tail_x = p.x - math.cos(a) * streak
                tail_y = p.y - math.sin(a) * streak
                # Brightness increases with distance
                bright = min(1.0, dist / (w * 0.3))
                cr.move_to(tail_x, tail_y)
                cr.line_to(p.x, p.y)
                cr.set_source_rgba(r, g, b, alpha * bright)
                cr.set_line_width(p.size)
                cr.stroke()
                # Bright dot at head
                cr.arc(p.x, p.y, p.size * 0.6, 0, 2 * math.pi)
                cr.set_source_rgba(1, 1, 1, alpha * bright * 0.8)
                cr.fill()
            elif ptype == 'scanline':
                # Horizontal bright line sweeping down
                cr.rectangle(0, p.y, w, p.size)
                cr.set_source_rgba(r, g, b, alpha * 0.4)
                cr.fill()
                # Brighter center line
                cr.rectangle(0, p.y + p.size * 0.3, w, p.size * 0.4)
                cr.set_source_rgba(r, g, b, alpha)
                cr.fill()
            elif ptype == 'glitch':
                # Random displaced rectangle
                gw = getattr(p, 'vx', 50)
                gh = getattr(p, 'vy', 6)
                cr.rectangle(p.x, p.y, gw, gh)
                # Shift color channels
                seed = getattr(p, 'seed', 0.5)
                if seed < 0.33:
                    cr.set_source_rgba(r, 0, 0, alpha)
                elif seed < 0.66:
                    cr.set_source_rgba(0, g, 0, alpha)
                else:
                    cr.set_source_rgba(0, 0, b, alpha)
                cr.fill()
                # Offset duplicate
                cr.rectangle(p.x + random.uniform(-5, 5),
                             p.y + random.uniform(-2, 2), gw, gh)
                cr.set_source_rgba(r, g, b, alpha * 0.3)
                cr.fill()
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
        self._done = set()  # block_ids that already finished animating

    def register(self, block_id):
        """Call when a block is first created/placed."""
        if block_id not in self._birth and block_id not in self._done:
            self._birth[block_id] = time.time()

    def get_alpha(self, block_id):
        """Return alpha 0..1 for fade-in. Returns 1.0 if not tracked or done."""
        birth = self._birth.get(block_id)
        if birth is None:
            return 1.0
        elapsed = time.time() - birth
        if elapsed >= self._DURATION:
            del self._birth[block_id]
            self._done.add(block_id)
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
/* PimpMyGRC toolbar styling */
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
"""
    return css.encode('utf-8')
