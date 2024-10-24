"""
https://stackabuse.com/brief-introduction-to-opengl-in-python-with-pyopengl/
"""
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu


def iterate():
    gl.glViewport(0, 0, 500, 500)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()


def showScreen(vertices):
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # Remove everything from screen (i.e. displays all white)
    gl.glLoadIdentity()
    iterate()
    gl.glColor3f(1.0, 0.0, 3.0)
    square(vertices)
    glut.glutSwapBuffers()


if __name__=='__main__':
    width = 500
    height = 500
    #START: drawing square
    vertices = (
        (100, 100),
        (200, 100),
        (200, 200),
        (100, 200)
    )
    #END: drawing square
    glut.glutInit()
    glut.glutInitDisplayMode(glut.GLUT_RGBA)
    glut.glutInitWindowSize(width, height)
    glut.glutInitWindowPosition(0, 0)
    wind = glut.glutCreateWindow("OpenGL Coding Practice")
    glut.glutDisplayFunc(showScreen)
    glut.glutIdleFunc(showScreen)
    glut.glutMainLoop()