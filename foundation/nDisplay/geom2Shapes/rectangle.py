import OpenGL.GL as gl

#2D shapes needed
# OVAL
# LINE
# TEXT
## http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial18.php # 2DFontPart1
## http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial19.php # 3D Font
## http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial20.php # 2DFontPart2

def rectangle(vertices):
    gl.glBegin(gl.GL_QUADS)
    for vertex in vertices:
        gl.glVertex2f(vertex[0], vertex[1])
    gl.glEnd()