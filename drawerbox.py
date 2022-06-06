#!/usr/bin/env python
# coding: utf8


# rackbox.py

# This is an Inkscape extension to generate internal slots in a box 
# It take an inkscape drawing with the slots drawn.
# Each "wall" should be a rectangle, only vertical or horizontal rectangles are allowed
# H and V rectangle could be adjacent, in this case the H (or V) wall will be attached to the V (or H) wall by notches
# H and H rectangles could also cross, in this case a mid-height assembly will be drawn.
# Written by Thierry Houdoin (thierry@fablab-lannion.org), June 2022

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from enum import Flag
import math
from numbers import Real
from operator import pos
import os.path
from typing import List
from more_itertools import last

from numpy import False_
import inkex
import simplepath
import simplestyle
import simpletransform
import re
from lxml import etree
from inkex import paths
from inkex import bezier
from th_inkscape_path import *

DEFAULT_WIDTH = 100
DEFAULT_HEIGHT = 100

CONTACT_LEFT = 1
CONTACT_RIGHT = 2
CONTACT_TOP = 4
CONTACT_BOTTOM = 8
NO_END_CONTACT = 0

#Global variables
burn_factor = 0.1
height = 50.0
BoundingBox = [ 100000000, 100000000, -100000000, -1000000000]
zNotches = 2
zNotchesSize = 10.0
thickness =3.0
hasbottom = False
BottomHoles = []

def DebugMsg(s):
    '''
    Print a debug message into debug file if debug file is defined
    '''
    if fDebug:
        fDebug.write(s)

def OpenDebugFile():
    global fDebug
    try:
        fDebug = open( 'DebugDrawerBox.txt', 'w')
    except IOError:
        pass
    DebugMsg("Start processing\n")

def CloseDebugFile():
    global fDebug
    if fDebug:
        fDebug.close()
        fDebug = None


class Contact:
    def __init__(self, start, end, direction):
        self.direction = direction
        self.start = start
        self.end = end

    def __str__(self):
        s = "Direction: " + str(self.direction) + " start:" + str(self.start) + " end:" + str(self.end) + '\n'
        return s

class wall:
    def __init__(self, id, x, y, w, h):
        self.id = id
        self.x0 = x
        self.y0 = y
        self.w = w
        self.h = h
        self.x1 = x + w
        self.y1 = y + h
        self.Contact = NO_END_CONTACT
        self.ContactList = []
        self.CrossList = []
        if ( h > w ):
            self.vertical = True
            self.length = h
        else:
            self.vertical = False
            self.length = w
    
    def __str__(self):
        s = "Wall id:" + self.id + " x0:" + str(self.x0) + " y0:" + str(self.y0) + " x1:" + str(self.x1) + " y1:" + str(self.y1) + " vertical:" + str(self.vertical) + '\n'
        s += "  EndContact: " + str(self.Contact) + '\n'
        s += "  Contact List :\n"
        for contact in self.ContactList:
            s += "   " + str(contact)
        s += '\n'
        s += "  Crossing(s):" + str(len(self.CrossList)) + "   Cross List :"
        for cross in self.CrossList:
            s += "   " + str(cross[0]) + "-" + str(cross[1])
        s += '\n'
        return s

    #   If the wall is vertical, sort by x then y
    #   If the wall is horizontal, sort by y then x
    def isLowerThan(self, elt):
        if self.vertical:
            if self.x0 < elt.x0:
                return True
            if self.x0 == elt.x0 and self.y0 < elt.y0:
                return True
            if self.x0 == elt.x0 and self.y0 == elt.y0: 
                inkex.errormsg("At least 2 walls with same starting point\n")
            return False
        else:
            if self.y0 < elt.y0:
                return True
            if self.y0 == elt.y0 and self.x0 < elt.x0:
                return True
            if self.y0 == elt.y0 and self.x0 == elt.x0: 
                inkex.errormsg("At least 2 walls with same starting point\n")
            return False

    #   Add the wall to the list of walls with the same orientation
    #   Insert the wall such as the list is sorted.
    #   If the wall is vertical, sort by x then y
    #   If the wall is horizontal, sort by y then x

    def add(self, ListWall):
        pos = 0
        for wall in ListWall:
            if self.isLowerThan(wall):
                break
            pos += 1
        ListWall.insert(pos, self)

    def AddContact(self, contact):
        pos = 0
        contact.start = round(contact.start, 1)
        contact.end = round(contact.end, 1)
        for c in self.ContactList:
            if contact.start <= c.start:
                break
            pos += 1
        self.ContactList.insert(pos, contact)

    #   Look for end contact with a wall in the other list
    #   End contact means contact between the short segments of the wall with a wall in the other list
    def LookForEndContact(self, ListWall):
        if self.vertical:
            #Begin with Top of wall
            #In this case, look for connection below H walls
            for w in ListWall:
                if self.y0 == w.y1:
                    if self.x0 > w.x0 and self.x0 < w.x1:
                        #There is a contact, compute starting and ending point
                        start_contact = self.x0 - w.x0
                        end_contact = min(self.x1, w.x1) - w.x0
                        self.Contact |= CONTACT_TOP
                        contact = Contact(start_contact, end_contact, CONTACT_TOP)
                        w.AddContact(contact)
                    elif self.x1 < w.x1 and self.x1 > w.x0:
                        #There is a contact, compute starting and ending point
                        start_contact = max(self.x0, w.x0) - w.x0
                        end_contact = self.x1 - w.x0
                        self.Contact |= CONTACT_TOP
                        contact = Contact(start_contact, end_contact, CONTACT_TOP)
                        w.AddContact(contact)
            #Then try Bottom, so look for connection above H walls
            for w in ListWall:
                if self.y1 == w.y0:
                    if self.x0 > w.x0 and self.x0 < w.x1:
                        #There is a contact, compute starting and ending point
                        start_contact = self.x0 - w.x0
                        end_contact = min(self.x1, w.x1) - w.x0
                        self.Contact |= CONTACT_BOTTOM
                        contact = Contact(start_contact, end_contact, CONTACT_BOTTOM)
                        w.AddContact(contact)
                    elif self.x1 < w.x1 and self.x1 > w.x0:
                        #There is a contact, compute starting and ending point
                        start_contact = max(self.x0, w.x0) - w.x0
                        end_contact = self.x1 - w.x0
                        self.Contact |= CONTACT_BOTTOM
                        contact = Contact(start_contact, end_contact, CONTACT_BOTTOM)
                        w.AddContact(contact)
        else:
            #Begin with left of wall
            #In this case, look for connection right of V walls
            for w in ListWall:
                if self.x0 == w.x1:
                    if self.y0 > w.y0 and self.y0 < w.y1:
                        #There is a contact, compute starting and ending point
                        start_contact = self.y0 - w.y0
                        end_contact = min(self.y1, w.y1) - w.y0
                        self.Contact |= CONTACT_LEFT
                        contact = Contact(start_contact, end_contact, CONTACT_LEFT)
                        w.AddContact(contact)
                    elif self.y1 < w.y1 and self.y1 > w.y0:
                        #There is a contact, compute starting and ending point
                        start_contact = max(self.y0, w.y0) - w.y0
                        end_contact = self.y1 - w.y0
                        self.Contact |= CONTACT_LEFT
                        contact = Contact(start_contact, end_contact, CONTACT_LEFT)
                        w.AddContact(contact)
            #Then try right, so look for connection left of V walls
            for w in ListWall:
                if self.x1 == w.x0:
                    if self.y0 > w.y0 and self.y0 < w.y1:
                        #There is a contact, compute starting and ending point
                        start_contact = self.y0 - w.y0
                        end_contact = min(self.y1, w.y1) - w.y0
                        self.Contact |= CONTACT_RIGHT
                        contact = Contact(start_contact, end_contact, CONTACT_RIGHT)
                        w.AddContact(contact)
                    elif self.y1 < w.y1 and self.y1 > w.y0:
                        #There is a contact, compute starting and ending point
                        start_contact = max(self.y0, w.y0) - w.y0
                        end_contact = self.y1 - w.y0
                        self.Contact |= CONTACT_RIGHT
                        contact = Contact(start_contact, end_contact, CONTACT_RIGHT)
                        w.AddContact(contact)
    
    #Look for crossing rectangles within the other side list.
    #Only one pass is needed, as this methode set up the 2 crossings
    #Should be called with self = H wall and List V Walls
    #The shortest wall will be with the top cut
    #As the list are sorted, no need to sort in the built list of crosspoints

    def LookForCrossContact(self,ListWall):
        HasCrossing = False
        TypeCrossing = False
        for w in ListWall:      #Try all V walls
            #They are crossing if...
            if self.x0 < w.x0 and self.x1 > w.x1 and self.y0 > w.y0 and self.y1 < w.y1:
                #All crossing of a wall should be the same, so copy the status of the first one
                if ( not HasCrossing  ):
                    locShort = self.length < w.length
                else:
                    locShort = TypeCrossing
                TypeCrossing = locShort
                HasCrossing = True
                #Compute local (H) crossPoint, only start point is needed as cut is always thickness wide
                locCrossPoint = (round(w.x0 - self.x0, 1), locShort)
                #Then distant (V) crosspoint
                remCrossPoint = (round(self.y0 - w.y0, 1), not locShort)
                self.CrossList.append(locCrossPoint)
                w.CrossList.append(remCrossPoint)


    def DrawWall(self, group, xpos, ypos):
        PositionInPage = [xpos, ypos]
        name = "wall" + self.id
        path = th_inkscape_path(PositionInPage, group, name)
        DebugMsg("Creating path("+name+") Position ="+str(PositionInPage)+'\n')
        path.MoveTo(0, 0)
        #Draw upper side, no notches, but could have crossing(s)
        for cross in self.CrossList:
            if cross[1]:
                path.LineTo(cross[0], 0)
                path.LineToVRel(height/2.0)
                path.LineToHRel(thickness)
                path.LineToVRel(-height/2.0)

        path.LineTo(self.length, 0)     #Go to end of line
        #Now draw right side, with notches if there is a contact
        if (self.Contact & CONTACT_RIGHT) or (self.Contact & CONTACT_TOP):
            for i in range(zNotches):
                path.LineTo(self.length, zNotchesSize + 2*i*zNotchesSize - burn_factor)
                path.LineToHRel(thickness)
                path.LineToVRel(zNotchesSize/2.0 + 2*burn_factor)
                path.LineToHRel(-thickness)
                path.LineToVRel(zNotchesSize/2.0)
        path.LineTo(self.length, height)
        #Now draw bottom side (reverse)
        #This line has notches (if bottom is present) and could have crossings
        lastPos = self.length
        for cross in reversed(self.CrossList):
            if not cross[1]:
                l = lastPos - cross[0] - thickness
                if  l < 20:
                    lNotches = 0
                    lNotchesSize = 0
                elif l < 30:
                    lNotches = 1
                    lNotchesSize = l / 3
                elif l < 100:
                    lNotches = int((l / 10.0 - 1)/2)
                    lNotchesSize = l / (2*lNotches + 1)
                elif l < 150:
                    lNotches = int((l / 15.0 - 1)/2)
                    lNotchesSize = l / (2*lNotches + 1)
                else:
                    lNotches = int((l / 20.0 - 1)/2)
                    lNotchesSize = l / (2*lNotches + 1)
                if  hasbottom:
                    for i in range(lNotches):
                        if self.vertical:
                            xStart = self.x0
                            xEnd = self.x1
                            yStart = self.y0 + lastPos - lNotchesSize - 2*i*lNotchesSize
                            yEnd = yStart - lNotchesSize
                        else:
                            xStart = self.x0 + lastPos - lNotchesSize - 2*i*lNotchesSize
                            xEnd = xStart - lNotchesSize
                            yStart = self.y0
                            yEnd = self.y1
                        path.LineTo(lastPos - lNotchesSize - 2*i*lNotchesSize + burn_factor, height)
                        path.LineToVRel(thickness)
                        path.LineToHRel(-lNotchesSize - 2*burn_factor)
                        path.LineToVRel(-thickness)
                        BottomHoles.append((xStart, yStart, xEnd, yEnd))
                path.LineTo(cross[0] + thickness, height)
                path.LineToVRel(-height/2.0)
                path.LineToHRel(-thickness)
                path.LineTo(cross[0], height)
                lastPos = cross[0]

        l = lastPos
        if  l < 20:
            lNotches = 0
            lNotchesSize = 0
        elif l < 30:
            lNotches = 1
            lNotchesSize = l / 3
        elif l < 100:
            lNotches = int((l / 10.0 - 1)/2)
            lNotchesSize = l / (2*lNotches + 1)
        elif l < 150:
            lNotches = int((l / 15.0 - 1)/2)
            lNotchesSize = l / (2*lNotches + 1)
        else:
            lNotches = int((l / 20.0 - 1)/2)
            lNotchesSize = l / (2*lNotches + 1)
        if  hasbottom:
            for i in range(lNotches):
                if self.vertical:
                    xStart = self.x0
                    xEnd = self.x1
                    yStart = self.y0 + lastPos - lNotchesSize - 2*i*lNotchesSize
                    yEnd = yStart - lNotchesSize
                else:
                    xStart = self.x0 + lastPos - lNotchesSize - 2*i*lNotchesSize
                    xEnd = xStart - lNotchesSize
                    yStart = self.y0
                    yEnd = self.y1
                path.LineTo(lastPos - lNotchesSize - 2*i*lNotchesSize + burn_factor, height)
                path.LineToVRel(thickness)
                path.LineToHRel(-lNotchesSize - 2*burn_factor)
                path.LineToVRel(-thickness)
                BottomHoles.append((xStart, yStart, xEnd, yEnd))
        path.LineTo(0, height)
        #then left side
        if (self.Contact & CONTACT_LEFT) or (self.Contact & CONTACT_BOTTOM):
            for i in range(zNotches):
                path.LineTo(0, height - zNotchesSize - 2*i*zNotchesSize + burn_factor)
                path.LineToHRel(-thickness)
                path.LineToVRel(-zNotchesSize/2.0 -2*burn_factor)
                path.LineToHRel(thickness)
                path.LineToVRel(-zNotchesSize/2.0)
        path.LineTo(0, 0)

        #Then draw holes if necessary
        for contact in self.ContactList:
            Offset = 0
            if contact.direction == CONTACT_LEFT or contact.direction == CONTACT_TOP:
                Offset = zNotchesSize/2.0
            for i in range(zNotches):
                path.MoveTo(contact.start, zNotchesSize + 2*i*zNotchesSize + Offset)
                path.LineToHRel(contact.end-contact.start)
                path.LineToVRel(zNotchesSize/2.0)
                path.LineToHRel(contact.start-contact.end)
                path.LineToVRel(-zNotchesSize/2.0)
        path.Close()
        path.GenPath()


class drawerbox( inkex.Effect ):

    def __init__( self ):
        inkex.Effect.__init__(self)
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']

        self.arg_parser.add_argument('--unit', action = 'store',
          type = str, dest = 'unit', default = 'mm',
          help = 'Unit, should be one of ')

        self.arg_parser.add_argument('--thickness', action = 'store',
          type = float, dest = 'thickness', default = '3.0',
          help = 'Material thickness')

        self.arg_parser.add_argument('--zc', action = 'store',
          type = float, dest = 'zc', default = '50.0',
          help = 'height')

        self.arg_parser.add_argument('--burn_factor', action = 'store',
          type = float, dest = 'burn_factor', default = '0.1',
          help = 'Laser burn factor')

        self.arg_parser.add_argument('--has_bottom', action = 'store',
          type = inkex.Boolean, dest = 'has_bottom', default = 'true',
          help = 'Gen bottom for drawer box')

        self.arg_parser.add_argument('--Mode_Debug', action = 'store',
          type = inkex.Boolean, dest = 'Mode_Debug', default = 'false',
          help = 'Output Debug information in file')

        # Debug Output file
        self.fDebug = None

        # Dictionary of warnings issued.  This to prevent from warning
        # multiple times about the same problem
        self.warnings = {}
        
        #Get bounding rectangle
        self.xmin, self.xmax = ( 1.0E70, -1.0E70 )
        self.ymin, self.ymax = ( 1.0E70, -1.0E70 )
        self.cx = float( DEFAULT_WIDTH ) / 2.0
        self.cy = float( DEFAULT_HEIGHT ) / 2.0


    try:
        inkex.Effect.unittouu   # unitouu has moved since Inkscape 0.91
    except AttributeError:
        try:
            def unittouu(self, unit):
                return inkex.unittouu(unit)
        except AttributeError:
            pass

    
    def DrawPoly(self, p, parent):
        group = etree.SubElement(parent, 'g')
        Newpath = inkcape_draw_cartesian((self.xmin - self.xmax - 10, 0), group)
        DebugMsg('DrawPoly First element (0) : '+str(p[0])+ ' Call MoveTo('+ str(p[0][0])+','+str(p[0][1])+'\n')
        Newpath.MoveTo(p[0][0], p[0][1])
        n = len( p )
        index = 1
        for point in p[1:n]:
            Newpath.LineTo(point[0], point[1])
            index += 1
        Newpath.GenPath()

    #   Add a wall (rectangle)
    #   x, y are the coordinates of the top left point, w and h are the width and length of the wall
    #   If w > h the wall is horizontal, otherwise it is vertical.
    #   Build a list of horizontal an vertical walls 
    def AddWall(self, id, x, y, w, h):
        Wall = wall(id, x, y, w, h)
        if ( w > h ):
            Wall.add(self.HorizontalWalls)
        else:
            Wall.add(self.VerticalWalls)



    def AddRectangle(self, x, y, w, h, id, transform):
        DebugMsg("Enter AddRectangle(id=" +id +") x=" + str(x) + ", y=" + str(y) + ", w=" + str(w) + ", h=" + str(h) + ', transform=' + str(transform) + '\n')
        Angle = 0
        if 'rotate' in transform:
            #DebugMsg("Transform contains rotate\n")
            pos_rotate =  transform.find('rotate(')
            #DebugMsg("pos_rotate= " + str(pos_rotate) + '\n')
            if ( pos_rotate >= 0 ):
                Start_Rotate = pos_rotate + 7
                EndRotate = transform.find(')', Start_Rotate)
                #DebugMsg("StartRotate="+ str(Start_Rotate) +", EndRotate= " + str(EndRotate) + '\n')
                if EndRotate > 0:
                    strAngle = transform[Start_Rotate:EndRotate]
                    Angle = float(strAngle)
                    #DebugMsg("Transform Rotate, Angle =" + str(Angle) + '\n')
                    Angle_rad = Angle * math.pi / 180

                    xrot1 = round(x*math.cos(Angle_rad) - y*math.sin(Angle_rad), 1)
                    yrot1 = round(x*math.sin(Angle_rad) + y*math.cos(Angle_rad), 1)
                    xrot2 =round((x+w)*math.cos(Angle_rad) - (y+h)*math.sin(Angle_rad), 1)
                    yrot2 = round((x+w)*math.sin(Angle_rad) + (y+h)*math.cos(Angle_rad), 1)
                    #DebugMsg("After Rotate, xrot1 =" + str(xrot1) +", yrot1 =" + str(yrot1) + ", xrot2 =" + str(xrot2) +", yrot2 =" + str(yrot2) + '\n')
                    xrect = min(xrot1, xrot2)
                    yrect = min(yrot1, yrot2)
                    wrect = abs(xrot1 - xrot2)
                    hrect = abs(yrot1 - yrot2)
                    DebugMsg("After Rotate, xrect =" + str(xrect) +", yrect =" + str(yrect) + ", wrect =" + str(wrect) +", hrect =" + str(hrect) + '\n')
        elif 'scale' in transform:
            DebugMsg("Transform contains scale\n")
            pos_scale =  transform.find('scale(')
            if ( pos_scale >= 0 ):
                Start_Scale = pos_scale + 6
                EndScaleX = transform.find(',', Start_Scale)
                EndScaleY = transform.find(')', Start_Scale)
                if EndScaleX > 0 and EndScaleY > 0:
                    strScaleX = transform[Start_Scale:EndScaleX]
                    strScaleY = transform[EndScaleX+1:EndScaleY]
                    ScaleX = float(strScaleX)
                    ScaleY = float(strScaleY)
                    xscale1 = round(x*ScaleX, 1)
                    yscale1 = round(y*ScaleY, 1)
                    xscale2 =round((x+w)*ScaleX, 1)
                    yscale2 = round((y+h)*ScaleY, 1)
                    DebugMsg("After Scale, xscale1 =" + str(xscale1) +", yscale1 =" + str(yscale1) + ", xscale2 =" + str(xscale2) +", yscale2 =" + str(yscale2) + '\n')
                    xrect = min(xscale1, xscale2)
                    yrect = min(yscale1, yscale2)
                    wrect = abs(xscale1 - xscale2)
                    hrect = abs(yscale1 - yscale2)
                    DebugMsg("After Rotate, xrect =" + str(xrect) +", yrect =" + str(yrect) + ", wrect =" + str(wrect) +", hrect =" + str(hrect) + '\n')
        elif transform == 'None':
            xrect = round(x, 1)
            yrect = round(y, 1)
            wrect = round(w, 1)
            hrect = round(h, 1)
        else:
            inkex.errormsg( 'Unhandled transformation :' + transform )
        self.AddWall(id, xrect, yrect, wrect, hrect)
        if ( xrect < BoundingBox[0] ):
            BoundingBox[0] = xrect
        if ( yrect < BoundingBox[1] ):
            BoundingBox[1] = yrect
        if ( xrect+wrect > BoundingBox[2] ):
            BoundingBox[2] = xrect + wrect
        if ( yrect+hrect > BoundingBox[3] ):
            BoundingBox[3] = yrect + hrect

    def recursivelyTraverseSvg( self, aNodeList):

        '''
        [ This too is largely lifted from eggbot.py and path2openscad.py ]

        Recursively walk the SVG document, building polygon vertex lists
        for each graphical element we support.

        Rendered SVG elements:
            <circle>, <ellipse>, <line>, <path>, <polygon>, <polyline>, <rect>
            Except for path, all elements are first converted into a path the processed

        Supported SVG elements:
            <group>

        Ignored SVG elements:
            <defs>, <eggbot>, <metadata>, <namedview>, <pattern>,
            processing directives

        All other SVG elements trigger an error (including <text>)
        '''

        for node in aNodeList:

            #DebugMsg("Node type :" + node.tag + '\n')
            if node.tag == inkex.addNS( 'g', 'svg' ) or node.tag == 'g':
                #DebugMsg("Group detected, recursive call\n")
                self.recursivelyTraverseSvg( node )

            elif node.tag == inkex.addNS( 'path', 'svg' ):
                DebugMsg("Path detected, skip object\n")

            elif node.tag == inkex.addNS( 'rect', 'svg' ) or node.tag == 'rect':

                # Create a path with the outline of the rectangle
                x = float( node.get( 'x' ) )
                y = float( node.get( 'y' ) )
                if ( not x ) or ( not y ):
                    pass
                w = float( node.get( 'width', '0' ) )
                h = float( node.get( 'height', '0' ) )
                id = node.get("id", "no_id")

                transform = node.get('transform', "None")

                #DebugMsg('Rectangle id='+id+', X='+ str(x)+',Y='+str(y)+', W='+str(w)+' H='+str(h)+', transform='+ transform+'\n' )
                self.AddRectangle(x, y, w, h, id, transform)


            elif node.tag == inkex.addNS( 'line', 'svg' ) or node.tag == 'line':

                DebugMsg('Line detected, skip\n' )

            elif node.tag == inkex.addNS( 'polyline', 'svg' ) or node.tag == 'polyline':

                DebugMsg('PolyLine detected, skip\n' )

            elif node.tag == inkex.addNS( 'polygon', 'svg' ) or node.tag == 'polygon':

                DebugMsg('Polygon detected, skip\n' )

            elif node.tag == inkex.addNS( 'ellipse', 'svg' ) or \
                node.tag == 'ellipse' or \
                node.tag == inkex.addNS( 'circle', 'svg' ) or \
                node.tag == 'circle':

                    DebugMsg('Ellipse or circle detected, skip\n' )

            elif node.tag == inkex.addNS( 'pattern', 'svg' ) or node.tag == 'pattern':

                pass

            elif node.tag == inkex.addNS( 'metadata', 'svg' ) or node.tag == 'metadata':

                pass

            elif node.tag == inkex.addNS( 'defs', 'svg' ) or node.tag == 'defs':

                pass

            elif node.tag == inkex.addNS( 'desc', 'svg' ) or node.tag == 'desc':

                pass

            elif node.tag == inkex.addNS( 'namedview', 'sodipodi' ) or node.tag == 'namedview':

                pass

            elif node.tag == inkex.addNS( 'eggbot', 'svg' ) or node.tag == 'eggbot':

                pass

            elif node.tag == inkex.addNS( 'text', 'svg' ) or node.tag == 'text':

                inkex.errormsg( 'Warning: unable to draw text, please convert it to a path first.' )

                pass

            elif node.tag == inkex.addNS( 'title', 'svg' ) or node.tag == 'title':

                pass

            elif node.tag == inkex.addNS( 'image', 'svg' ) or node.tag == 'image':

                if not self.warnings.has_key( 'image' ):
                    inkex.errormsg( gettext.gettext( 'Warning: unable to draw bitmap images; ' +
                        'please convert them to line art first.  Consider using the "Trace bitmap..." ' +
                        'tool of the "Path" menu.  Mac users please note that some X11 settings may ' +
                        'cause cut-and-paste operations to paste in bitmap copies.' ) )
                    self.warnings['image'] = 1
                pass

            elif node.tag == inkex.addNS( 'pattern', 'svg' ) or node.tag == 'pattern':

                pass

            elif node.tag == inkex.addNS( 'radialGradient', 'svg' ) or node.tag == 'radialGradient':

                # Similar to pattern
                pass

            elif node.tag == inkex.addNS( 'linearGradient', 'svg' ) or node.tag == 'linearGradient':

                # Similar in pattern
                pass

            elif node.tag == inkex.addNS( 'style', 'svg' ) or node.tag == 'style':

                # This is a reference to an external style sheet and not the value
                # of a style attribute to be inherited by child elements
                pass

            elif node.tag == inkex.addNS( 'cursor', 'svg' ) or node.tag == 'cursor':

                pass

            elif node.tag == inkex.addNS( 'color-profile', 'svg' ) or node.tag == 'color-profile':

                # Gamma curves, color temp, etc. are not relevant to single color output
                pass

            elif not isinstance( node.tag, basestring ):

                # This is likely an XML processing instruction such as an XML
                # comment.  lxml uses a function reference for such node tags
                # and as such the node tag is likely not a printable string.
                # Further, converting it to a printable string likely won't
                # be very useful.

                pass

            else:

                inkex.errormsg( 'Warning: unable to draw object <%s>, please convert it to a path first.' % node.tag )
                pass


    def effect( self ):
        global thickness, hasbottom, burn_factor, height, zNotches, zNotchesSize
        # convert units
        unit = self.options.unit
        thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        height = self.svg.unittouu(str(self.options.zc) + unit)
        burn_factor = self.svg.unittouu(str(self.options.burn_factor) + unit)
        hasbottom = self.options.has_bottom

        svg = self.document.getroot()
        docWidth = self.svg.unittouu(svg.get('width'))
        docHeigh = self.svg.unittouu(svg.attrib['height'])
        self.HorizontalWalls = []
        self.VerticalWalls = []
        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'DrawerBox')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        self.group = etree.SubElement(layer, 'g')

        OpenDebugFile()
       

        # First traverse the document (or selected items), reducing
        # everything to line segments.  If working on a selection,
        # then determine the selection's bounding box in the process.
        # (Actually, we just need to know it's extrema on the x-axis.)

        # Traverse the selected objects
        for id in self.options.ids:
            self.recursivelyTraverseSvg( [self.svg.selected[id]] ) 

        #   Now for each H wall, look for end contact with a V wall
        for w in self.HorizontalWalls:
            w.LookForEndContact(self.VerticalWalls)

        #   Now for each V wall, look for end contact with a H wall
        for w in self.VerticalWalls:
            w.LookForEndContact(self.HorizontalWalls)

        DebugMsg("After End contact\n  Horizontal walls :" + str(len(self.HorizontalWalls)) + '\n')
        for w in self.HorizontalWalls:
            DebugMsg(str(w))
        DebugMsg("Vertical walls :" + str(len(self.VerticalWalls)) + '\n')
        for w in self.VerticalWalls:
            DebugMsg(str(w))

        DebugMsg("Fin contact\n")

        
        for w in self.HorizontalWalls:
            w.LookForCrossContact(self.VerticalWalls)
        DebugMsg("After Cross contact\n Horizontal walls :" + str(len(self.HorizontalWalls)) + '\n')
        for w in self.HorizontalWalls:
            DebugMsg(str(w))
        DebugMsg("Vertical walls :" + str(len(self.VerticalWalls)) + '\n')
        for w in self.VerticalWalls:
            DebugMsg(str(w))
        
        # After this step, generate the walls

        # Compute the number of notches from the height

        if ( height < 30.0 ):
            zNotches = 1
        elif ( height < 70.0 ):
            zNotches = 2
        elif ( height < 110.0 ):
            zNotches = 3
        else:
            zNotches = 4
        zNotchesSize = height / ( 2.0*zNotches + 1.0 )
        ypos = -BoundingBox[3] - 10
        xpos = -BoundingBox[0]

        for w in self.HorizontalWalls:
            DebugMsg("Draw H Wall " + w.id + " ypos =" + str(ypos) + '\n')
            w.DrawWall(self.group, xpos, ypos)
            ypos -= height + thickness + 3

        for w in self.VerticalWalls:
            DebugMsg("Draw V Wall " + w.id + " ypos =" + str(ypos) + '\n')
            w.DrawWall(self.group, xpos, ypos)
            ypos -= height + thickness + 3

        #And last the bottom layer, if needed
        if hasbottom:
            PositionInPage = [xpos, ypos]
            path = th_inkscape_path(PositionInPage, self.group, "Bottom")
            path.MoveTo(0, 0)
            #First draw the exterior
            path.LineToHRel(BoundingBox[2] - BoundingBox[0])
            path.LineToVRel(BoundingBox[3] - BoundingBox[1])
            path.LineToHRel(BoundingBox[0] - BoundingBox[2])
            path.LineTo(0, 0)
            #then the holes
            for hole in BottomHoles:
                path.MoveTo(hole[0]- BoundingBox[0], hole[1] - BoundingBox[1])
                path.LineTo(hole[2]- BoundingBox[0], hole[1] - BoundingBox[1])
                path.LineTo(hole[2]- BoundingBox[0], hole[3] - BoundingBox[1])
                path.LineTo(hole[0]- BoundingBox[0], hole[3] - BoundingBox[1])
                path.LineTo(hole[0]- BoundingBox[0], hole[1] - BoundingBox[1])
            path.Close()
            path.GenPath()

        CloseDebugFile()

if __name__ == '__main__':

    e = drawerbox()
    e.run()
