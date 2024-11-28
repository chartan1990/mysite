import math
import OpenGL.GL as gl

def draw_ellipse(center1, center2, radius1, radius2, segments=100):
    """
    Copied from ChatGPT
    """
    # Calculate the center of the ellipse
    cx = (center1[0] + center2[0]) / 2
    cy = (center1[1] + center2[1]) / 2

    # Calculate the radii (use the larger radius as the major axis)
    rx = abs(center2[0] - center1[0]) / 2
    ry = abs(center2[1] - center1[1]) / 2

    # Use the specified radii instead of recalculated ones if provided
    if radius1 and radius2:
        rx, ry = radius1, radius2

    gl.glBegin(gl.GL_TRIANGLE_FAN)
    gl.glVertex2f(cx, cy)  # Center of the ellipse
    for i in range(segments + 1):
        theta = 2.0 * math.pi * i / segments
        x = cx + rx * math.cos(theta)
        y = cy + ry * math.sin(theta)
        gl.glVertex2f(x, y)
    gl.glEnd()