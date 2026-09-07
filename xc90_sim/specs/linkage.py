"""
3D suspension linkage hardpoints — front double-wishbone, rear multi-link
("Integral Axle") modeled as an equivalent 2-arm swing-arm system (a
multi-link's several links reduce, for basic kinematic analysis, to an
effective upper/lower arm pair — a standard simplification, not a full
multi-link solve).

No real Volvo hardpoint coordinates are published (this is proprietary CAD
data), so every coordinate here is ASSUMPTION. They were solved (not
guessed freehand) to land the resulting geometry in plausible real-world
K&C ranges: front roll center 100mm / rear 150mm above ground (typical
crossover range 60-200mm), front camber gain ~2.9 deg / rear ~1.4 deg over
80mm of travel (typical double-wishbone/multi-link full-travel range 2-4
deg), front anti-dive ~15% / rear anti-squat ~16% (typical passenger-car
range 10-30%) — see suspension/linkage_geometry.py for the derivation.

Coordinate frame, all relative to the wheel center at static ride height:
  Front view (for camber/roll center): y = outboard+, z = up+
  Side view  (for anti-dive/squat):    x = forward+,  z = up+
"""

# --- Front view (y, z): outboard ball joint and inboard chassis pivot ---
FRONT_UPPER_BALL_JOINT_YZ = (0.0, 0.10)
FRONT_UPPER_PIVOT_YZ = (-0.2402, 0.0306)
FRONT_LOWER_BALL_JOINT_YZ = (0.0, -0.20)
FRONT_LOWER_PIVOT_YZ = (-0.4477, -0.2453)

REAR_UPPER_BALL_JOINT_YZ = (0.0, 0.08)
REAR_UPPER_PIVOT_YZ = (-0.2925, 0.0135)
REAR_LOWER_BALL_JOINT_YZ = (0.0, -0.15)
REAR_LOWER_PIVOT_YZ = (-0.5435, -0.2344)

# --- Side view (x, z): for anti-dive (front) / anti-squat (rear) ---
# Represented via the lower arm only (the dominant contributor in most SLA
# designs) — pivot behind-and-above (front) or ahead-and-above (rear) the
# wheel center, which is what gives genuine anti-dive/anti-squat geometry.
FRONT_LOWER_BALL_JOINT_XZ = (0.0, -0.20)
FRONT_LOWER_PIVOT_XZ = (-0.20, -0.17)

REAR_LOWER_BALL_JOINT_XZ = (0.0, -0.15)
REAR_LOWER_PIVOT_XZ = (0.25, -0.11)
