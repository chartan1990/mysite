import OpenGL.GLU as glu


def partialDisk(internalRadius, externalRadius, slices, rings, startAngle, angle, drawStyle):
	partialDiskQ = glu.gluNewQuadric()
	gl.glPushMatrix() # save first position
	glu.gluQuadricDrawStyle(partialDiskQ, drawStyle)
	#https://learn.microsoft.com/en-us/windows/win32/opengl/glupartialdisk
	#https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluPartialDisk.xml
	glu.gluPartialDisk(partialDiskQ, internalRadius, externalRadius, slices, rings, startAngle, angle)
	#glu.gluDeleteQuadric(partialDiskQ);
	gl.glPopMatrix() # load first position



#DEV TEST
if __name__=='__main__':
	from foundation.nDisplay.core.stage import Stage
	def piece():
		internalRadius = 5.0
		externalRadius = 9.0
		slices = 3
		rings = 3
		startAngle = 0
		angle = 20
		drawStyle = glu.GLU_FILL
		partialDisk(internalRadius, externalRadius, slices, rings, startAngle, angle, drawStyle)
	width = 800
	height = 600
	metronome = 10
	displayCaption = "PartialDisk testing"
	fieldOfView = 45
	zNear = 0.1
	zFar = 50
	verbose = False
	stage = Stage(width, height, piece, metronome, displayCaption, fieldOfView, zNear, zFar, verbose)