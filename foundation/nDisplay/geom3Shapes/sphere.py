"""

https://stackoverflow.com/questions/5988686/creating-a-3d-sphere-in-opengl-using-visual-c/5989676#5989676  <<<jagged sphere

http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial7.php  <<< has 'cut-and-paste code' for sphere... but pyGame library does not have those functions?
"""
import OpenGL.GLU as glu

def sphere(radius, slices, rings, drawStyle):
	sphereQ = glu.gluNewQuadric()
	gl.glPushMatrix() # save first position
	glu.gluQuadricDrawStyle(sphereQ, drawStyle)
	#https://learn.microsoft.com/en-us/windows/win32/opengl/glusphere
	#https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluSphere.xml
	glu.gluSphere(sphereQ, radius, slices, rings) 
	#glu.gluDeleteQuadric(sphereQ);
	gl.glPopMatrix() # load first position



#DEV TEST
if __name__=='__main__':
	from foundation.nDisplay.core.stage import Stage
	def piece():
		radius = 0.5
		slices = 20
		rings = 20
		drawStyle = glu.GLU_FILL
		sphere(radius, slices, rings, drawStyle)
	width = 800
	height = 600
	metronome = 10
	displayCaption = "Sphere testing"
	fieldOfView = 45
	zNear = 0.1
	zFar = 50
	verbose = False
	stage = Stage(width, height, piece, metronome, displayCaption, fieldOfView, zNear, zFar, verbose)