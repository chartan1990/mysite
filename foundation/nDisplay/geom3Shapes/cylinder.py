import OpenGL.GL as gl
import OpenGL.GLU as glu


def cylinder(baseRadius, topRadius, height, slices, stacks, drawStyle):
	"""
	From http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial7.php

	#defines if the shape is textured
	glu.gluQuadricTexture(quadric, value) #Default: false
	#defines the rendering style of the quadric
	glu.gluQuadricDrawStyle(quadric, value) #Default: GLU_FILL
	#defines if the shape is drawn with normal and, if so, specify if it is per face or per vertex normal
	glu.gluQuadricNormals(quadric, value) #Default: GLU_SMOOTH
	#defines normal orientation, either points outside the shape or inside
	glu.gluQuadricOrientation(quadric, value) # Default: GLU_OUTSIDE


	http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial7.php


	Mostly just a wrapper for glu.cylinder, more details here:

	#https://learn.microsoft.com/en-us/windows/win32/opengl/glucylinder
	#https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluCylinder.xml



	gluQuadricTexture True/False
	gluQuadricNormals GLU_NONE / GLU_FLAT / GLU_SMOOTH
	gluQuadricOrientation GLU_OUTSIDE / GLU_INSIDE

	:param baseRadius:
	:type baseRadius:
	
	:param topRadius:
	:type topRadius:
	
	:param height:
	:type height:
	
	:param slices:
	:type slices:
	
	:param stacks:
	:type stacks:
	
	:param drawStyle:
	more information here:

	https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluQuadricDrawStyle.xml
	https://learn.microsoft.com/en-us/windows/win32/opengl/gluquadricdrawstyle
	https://www.ibm.com/docs/sl/aix/7.1?topic=library-gluquadricdrawstyle-subroutine


	valid enums for the second argument of glu:-
	import OpenGL.GLU as glu
	glu.GLU_FILL
	glu.GLU_LINE
	glu.GLU_SILHOUETTE
	glu.GLU_POINT
	:type drawStyle: :class:`OpenGL.constant.IntConstant`

	"""
	cylinderQ = glu.gluNewQuadric()
	gl.glPushMatrix() # save first position
	glu.gluQuadricTexture(cylinderQ, True)
	glu.gluQuadricDrawStyle(cylinderQ, drawStyle)
	glu.gluQuadricNormals
	glu.gluCylinder(cylinderQ, baseRadius, topRadius, height, slices, stacks)
	#glu.gluDeleteQuadric(cylinderQ);
	gl.glPopMatrix() # load first position


def cone(drawStyle):
	coneQ = glu.gluNewQuadric()
	gl.glPushMatrix() # save first position
	glu.gluQuadricDrawStyle(coneQ, drawStyle)
	#https://learn.microsoft.com/en-us/windows/win32/opengl/glucylinder
	#https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluCylinder.xml
	glu.gluCylinder(coneQ, 0.6, 0, 2.5, 20, 20) # according to this: http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial7.php
	#glu.gluDeleteQuadric(coneQ);
	gl.glPopMatrix() # load first position


#DEV TEST
if __name__=='__main__':
	from foundation.nDisplay.core.stage import Stage
	def piece():
		baseRadius = 1
		topRadius = 1
		height = 3
		slices = 20
		stacks = 20
		drawStyle = glu.GLU_FILL
		cylinder(baseRadius, topRadius, height, slices, stacks, drawStyle)
	width = 800
	height = 600
	metronome = 10
	displayCaption = "Cylinder testing"
	fieldOfView = 45
	zNear = 0.1
	zFar = 50
	verbose = False
	stage = Stage(width, height, piece, metronome, displayCaption, fieldOfView, zNear, zFar, verbose)