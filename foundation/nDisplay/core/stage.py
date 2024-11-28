from copy import deepcopy
import math
import sys

import pygame as pg
import pygame.locals as pl
import OpenGL.GL as gl
import OpenGL.GLU as glu

from foundation.nDisplay.common import convertToPyArray
from foundation.nDisplay.controlsMapping import KEYBOARD_3D_DISPLAY_CONTROLS as KBCM

#TODO more Geometric shapes that components need
#TODO shining Geometric shapes to mimic flow of current : http://jerome.jouvie.free.fr/opengl-tutorials/Tutorial9.php

class Stage:

    def __init__(self, width, height, piece, metronome, displayCaption, fieldOfView, zNear, zFar, verbose):
        """
        :param width: width of the viewport (screen of the program)
        :type width: float
        :param height: height of the viewport (screen of the program)
        :type height: float

        :param piece: like the script of a movie or the score of a orchestration. Instructions for where to put piece,
        how they move, etc...
        :type piece: Callable

        :param metronome: frames-per-second
        :type metronome: float
        :param displayCaption: title of the screen
        :type displayCaption: str

        :param fieldOfView:
        This is the wideness of the Frustrum - the width of the whole stage

        For more information see here:
        https://registry.khronos.org/OpenGL-Refpages/gl2.1/xhtml/gluPerspective.xml
        -here is one with a diagram of a view frustum:
        https://www.songho.ca/opengl/gl_transform.html#example1

        0 to 360

        :type fieldOfView: float
        :param zNear: distance from most forefront of the stage to the eye. front of the stage. first clipping plane
        :type zNear: float
        :param zFar: distance from most backend of the stage to the eye. back of the stage. last clipping plane
        :type zFar: float
        :param verbose: show i display all processing?
        :type verbose: bool
        """
        self.width = width
        self.height = height
        self.piece = piece
        self.metronome = metronome
        self.displayCaption = displayCaption
        self.fieldOfView = fieldOfView
        self.zNear = zNear
        self.zFar = zFar
        self.verbose = verbose
        self.resetted = False
        self.resetting = False
        self._initScene()
        #state variables
        self.mouseDown = False
        self.mouseDownPos = None # tuple(x, y)
        self._action()

    def _initScene(self):
        pg.init()
        self._displayInit()

    def _displayInit(self):
        pg.display.set_mode((self.width, self.height), pg.DOUBLEBUF|pg.OPENGL)
        pg.display.set_caption(self.displayCaption)
        self.aspectRatio = float(self.width)/float(self.height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity() # remove accumulated transformations
        glu.gluPerspective(
            self.fieldOfView,
            self.aspectRatio,
            self.zNear,
            self.zFar
        )
        gl.glTranslatef(0.0, 0.0, -5) # initial zoom out... TODO configurable/ calculated to give 'BEST initial VIEW of the stage'


    def _action(self):
        """
        ACTION! starts the scene rolling.

        :param piece:
        :type piece:
        :param metronome:
        :type metronome:
        :param verbose:
        :type verbose:

        event: function that runs continuously, dictating what happens on the screen
        metronome: 1/fps (frame per second)
        """
        clock = pg.time.Clock()
        running = True
        while running:
            for event in pg.event.get():
                #quit event handling
                if event.type == pg.QUIT:
                    running = False
                #
                self._mouseHandler(event)
                self._keyboardHandler(event)
            if self.resetting:
                #pg.display.quit() # this closes the window
                #pg.display.init()
                #STENCIL is used for storing pixel data coming from reflection of light
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # GL_ACCUM_BUFFER_BIT GL_STENCIL_BUFFER_BIT
                self._displayInit()
                self.resetting = False
                if self.verbose:
                    print('resetted............')
                self.resetted = True
            else:
                if not self.resetted:
                    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT) # cannot call glClear while pg.display.init
                else:
                    self.resetted = False
                    if self.verbose:
                        print('unresetted..............')
                self.piece()
                pg.display.flip()
            clock.tick(self.metronome)#pg.time.wait(metronome)
        pg.quit()
        sys.exit() # comes with clean-up from 'finally' # https://www.geeksforgeeks.org/python-exit-commands-quit-exit-sys-exit-and-os-_exit/
        #os.exit(os.EX_OK) # sub-pub for multithreading/processing, wait for other thread/process to finish

    def _mouseHandler(self, event):
        """

        :param event:
        :type event:
        """
        if event.type == pg.MOUSEBUTTONDOWN:
            self.mouseDownPos = pg.mouse.get_pos()
            self.mouseDown = True
            if self.verbose:
                print(self.mouseDownPos, "FIRST mouse button down")
                self.printModelProjView()
        if event.type == pg.MOUSEBUTTONUP:
            self.mouseDown = False
            if self.verbose:
                print(self.mouseDown, "mouse button up")
        if self.mouseDown and event.type == pg.MOUSEMOTION:
            rel = pg.mouse.get_rel()
            btn = pg.mouse
            #TODO formulas should be configurable.... on a seperate configurable... file?
            # actually just a magnitude, user can adjust sensitivity 
            #math.atan(abs(rel[1])/abs(rel[0])) if rel[0] != 0.0 else 0 
            def angleF(): #TODO UI can be improved, vertical drag up and horizontal drag up a little weird...
                if rel[0] == 0.0 and rel[1] == 0.0:
                    return 0
                elif rel[0] == 0.0:
                    return 1.0/(KBCM['screen_out_sensitivity']+abs(rel[0]/rel[1]))
                else:
                    return 1.0/(KBCM['screen_out_sensitivity']+abs(rel[1]/rel[0]))
            xSign = abs(rel[0])/rel[0] if rel[0] != 0.0 else 1
            ySign = abs(rel[1])/rel[1] if rel[1] != 0.0 else 1
            zSign = abs(rel[0] * rel[1]) / (rel[0] * rel[1]) if rel[0] != 0.0 and rel[1] != 0.0 else 0# could also be 0 if rel[0] == 0.0 or rel[1] == 0.0 else xSign*ySign, depends on the processor, does 'or/==' cost more than multiply? (does logical operators cost more than arithmetic operators (processor specific configurations?)?)
            originVecVerViewPort = self.getPrickVerViewPort()
            gl.glRotatef(angleF(), ySign*originVecVerViewPort[0], xSign*originVecVerViewPort[1], zSign*originVecVerViewPort[2])
            if self.verbose:
                print(rel, angleF(), xSign, ySign, zSign)

    def _keyboardHandler(self, event):
        """

        :param event:
        :type event:
        """
        if event.type == pg.KEYDOWN:
            ## screen related
            if event.key == KBCM['screen_left']:
                gl.glTranslatef(-KBCM['screen_left_sensitivity'], 0, 0)
                if self.verbose:
                    print("left")
            if event.key == KBCM['screen_right']:
                gl.glTranslatef(KBCM['screen_right_sensitivity'], 0, 0)
                if self.verbose:
                    print("right")
            if event.key == KBCM['screen_up']:
                gl.glTranslatef(0, KBCM['screen_up_sensitivity'], 0)
                if self.verbose:
                    print("up")
            if event.key == KBCM['screen_down']:
                gl.glTranslatef(0, -KBCM['screen_down_sensitivity'], 0)
                if self.verbose:
                    print("down")
            if event.key == KBCM['screen_in']:
                gl.glTranslatef(0, 0, KBCM['screen_in_sensitivity'])
                if self.verbose:
                    print("in")
            if event.key == KBCM['screen_out']:
                gl.glTranslatef(0, 0, -KBCM['screen_out_sensitivity'])
                if self.verbose:
                    print("out")
            ## screen related
            if event.key == KBCM['actor_reset']: #TODO this does not work, not sure why
                self.resetting = True
                if self.verbose:
                    print('actor reset')

    #GETTERS of stage
    def getPythonicModelViewMatrix(self):
        """
        
        """
        model = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
        return convertToPyArray(deepcopy(model))


    def getPythonicProjectionMatrix(self):
        """

        """
        proj = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
        return convertToPyArray(deepcopy(proj))

    def getPythonicViewport(self):
        """

        """
        view = gl.glGetDoublev(gl.GL_VIEWPORT)
        return convertToPyArray(deepcopy(view))


    def getPrickVerViewPort(self):
        """
        Get the prick(vector from origin) towards(ver) me(viewport)
        """
        pyModel = self.getPythonicModelViewMatrix()
        #get the vectors of x-axis, y-axis, z-axis and return a linear combination
        xAxisVector = [pyModel[0][0], pyModel[1][0], pyModel[2][0]]
        yAxisVector = [pyModel[0][1], pyModel[1][1], pyModel[2][1]]
        zAxisVector = [pyModel[0][2], pyModel[1][2], pyModel[2][2]]
        lcVector = []
        for idx in range(0, 3):
            lci = xAxisVector[idx] + yAxisVector[idx] + zAxisVector[idx]
            lcVector.append(lci)
        return lcVector

    def printModelProjView(self):
        """
        print the states of this stage, 
        Model
        Projection
        View
        """
        model = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
        proj = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
        view = gl.glGetDoublev(gl.GL_VIEWPORT)
        ####
        pyModel = convertToPyArray(deepcopy(model))
        pyProj = convertToPyArray(deepcopy(proj))
        pyView = convertToPyArray(deepcopy(view))
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print('model-------')
        # pp.pprint(pyModel)
        # print('projection-------')
        # pp.pprint(pyProj)
        # print('view-----------')
        # pp.pprint(pyView)

