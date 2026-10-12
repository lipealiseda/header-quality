"""Small pitch geometry helpers. StatsBomb pitch is 120 x 80 and the acting team
always attacks toward x = 120. Goal posts sit at y = 36 and y = 44."""
import numpy as np

GOAL_X = 120.0
POST_L, POST_R = 36.0, 44.0
GOAL_CENTER = np.array([120.0, 40.0])


def dist_to_goal(x, y):
    return np.hypot(GOAL_X - x, 40.0 - y)


def goal_angle(x, y):
    """Angle in degrees that the goal mouth opens up from (x, y). Bigger is easier."""
    a = np.arctan2(POST_R - y, GOAL_X - x)
    b = np.arctan2(POST_L - y, GOAL_X - x)
    ang = np.abs(a - b)
    return np.degrees(ang)


def in_box(x, y):
    return (x >= 102) & (y >= 18) & (y <= 62)


def in_six(x, y):
    return (x >= 114) & (y >= 30) & (y <= 50)


def in_own_box(x, y):
    return (x <= 18) & (y >= 18) & (y <= 62)


def point_in_triangle(p, a, b, c):
    """True if point p is inside triangle abc (all 2D arrays)."""
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = sign(p, a, b), sign(p, b, c), sign(p, c, a)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def angle_between(v1, v2):
    """Unsigned angle in degrees between two 2D vectors."""
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return np.nan
    cosv = np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1)
    return float(np.degrees(np.arccos(cosv)))
