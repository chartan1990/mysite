import OpenGL.GL as gl

def rectangle(vertices):
    gl.glBegin(gl.GL_QUADS)
    for vertex in vertices:
        gl.glVertex2f(vertex[0], vertex[1])
    gl.glEnd()