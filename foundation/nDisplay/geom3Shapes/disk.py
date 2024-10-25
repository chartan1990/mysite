import OpenGL.GLU as glu


def disk(internalRadius, externalRadius, slices, rings, drawStyle):
	diskQ = glu.gluNewQuadric()
	gl.glPushMatrix() # save first position
	glu.gluQuadricDrawStyle(diskQ, drawStyle)
	#https://learn.microsoft.com/en-us/windows/win32/opengl/gludisk
	#https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluDisk.xml
	glu.gluDisk(diskQ, internalRadius, externalRadius, slices, rings)
	#glu.gluDeleteQuadric(diskQ);
	gl.glPopMatrix() # load first position



#TODO actually a resistor is more like a long long disk?
#DEV TEST
if __name__=='__main__':
	from foundation.nDisplay.core.stage import Stage
	def piece():
		internalRadius = 5.0
		externalRadius = 9.0
		slices = 3
		rings = 3
		drawStyle = glu.GLU_FILL
		disk(internalRadius, externalRadius, slices, rings, drawStyle)
	width = 800
	height = 600
	metronome = 10
	displayCaption = "Disk testing"
	fieldOfView = 45
	zNear = 0.1
	zFar = 50
	verbose = False
	stage = Stage(width, height, piece, metronome, displayCaption, fieldOfView, zNear, zFar, verbose)