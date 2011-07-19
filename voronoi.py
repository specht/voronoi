#! /usr/bin/env python

import math
import copy
import random
from pysvg.structure import *
from pysvg.shape import *
import heapq

random.seed(2000)

N = 6
WIDTH = 500
HEIGHT = 500
MAX_LENGTH = 2000
BORDER = 50

SITE_EVENT = 1
CIRCLE_EVENT = 2
INF = float('inf')
MINUS_INF = float('-inf')

outline = []


class Struct:
    def __repr__(self):
        result = []
        for k, v in vars(self).iteritems():
            result.append(str(k) + ': ' + str(v))
        return '(' + ', '.join(result) + ')'
        
        
class Vector:
    def __init__(self, _x, _y):
        self.x = _x
        self.y = _y

    def len2(self):
        return self.x * self.x + self.y * self.y

    def len(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
        
    def __mul__(self, f):
        if type(f) == type(self):
            return (self.x * f.x) + (self.y * f.y)
        else:
            return Vector(self.x * f, self.y * f)
        
    def __repr__(self):
        return '(' + ('%1.2f' % self.x) + ', ' + ('%1.2f' % self.y) + ')'
        
    def rotate90(self):
        return Vector(-self.y, self.x)
        
    def normalized(self):
        l = self.len()
        return self * (1.0 / l)
        
        
class Site(Vector):
    def __init__(self, _x, _y, _label = ''):
        Vector.__init__(self, _x, _y)
        self.label = _label
        
    def __repr__(self):
        return "[{label}]: {p}".format(label = self.label, p = Vector.__repr__(self))
        
        
class BeachSpan:
    def __init__(self, _site):
        self.circleEvent = None
        self.site = _site
        self.__prev = None
        self.__next = None
        
    def setPrev(self, x):
        self.__prev = x
        
    def getPrev(self):
        return self.__prev
        
    prev = property(getPrev, setPrev)
        
    def setNext(self, x):
        self.__next = x
        
    def getNext(self):
        return self.__next
        
    next = property(getNext, setNext)
    
    def __repr__(self):
        return '(span ' + str(self.site.label) + ')'

class BeachLine:
    def __init__(self):
        self.spans = []
        
    def handleSiteEvent(self, _event):
        sweepy = _event.y
        span = BeachSpan(_event.site)
        if len(self.spans) == 0:
            # there is no span yet
            self.spans.append(span)
        else:
            # use binary search to insert new span at the correct position
            l = 0
            r = len(self.spans) - 1
            while l < r:
                # binary search
                m = (r - l) // 2 + l
                mr = INF
                if m < len(self.spans) - 1:
                    mr = self.beachSpanIntersection(self.spans[m], self.spans[m + 1], sweepy)
                if span.site.x < mr:
                    r = m
                else:
                    l = m + 1
                    
            # duplicate span and insert the copy
            self.spans.insert(l + 1, copy.copy(self.spans[l]))
            self.spans[l].next = self.spans[l + 1]
            self.spans[l + 1].prev = self.spans[l]
            
            # insert the new span
            span.prev = self.spans[l]
            span.next = self.spans[l + 1]
            self.spans[l].next = span
            self.spans[l + 1].prev = span
            self.spans.insert(l + 1, span)
            
            # now check whether there are new circle events (shrinking spans)
            newSpanIndex = l + 1
            if newSpanIndex > 1:
                # check triplet left to new span
                self.checkPotentialCircleEvent(self.spans[newSpanIndex - 1])
            if newSpanIndex < len(self.spans) - 2:
                # check triplet right to new span
                self.checkPotentialCircleEvent(self.spans[newSpanIndex + 1])
            
    def handleCircleEvent(self, _circle):
        pass
    
    def beachSpanIntersection(self, a, b, sweepy):
        pby2 = b.site.y - sweepy
        if (pby2 == 0.0):
            return b.site.x
            
        plby2 = a.site.y - sweepy
        if (plby2 == 0.0):
            return a.site.x
            
        hl = a.site.x - b.site.x
        aby2 = 1.0 / pby2 - 1.0 / plby2
        bb = hl / plby2
        
        if (aby2 != 0):
            return (-bb + math.sqrt(bb * bb - 2.0 * aby2 * (hl * hl / (-2 * plby2) - a.site.y + plby2 / 2 + b.site.y - pby2 / 2))) / aby2 + b.site.x
        return (a.site.x + b.site.x) / 2
        
    def checkPotentialCircleEvent(self, _span):
        print("Checking for potential circle event at", _span.prev, _span, _span.next)
        
    def __repr__(self):
        return ', '.join([str(_) for _ in self.spans])

class Event:
    def __init__(self, _y):
        self.y = _y
        
    def __cmp__(self, other):
        return self.y - other.y


class SiteEvent(Event):
    def __init__(self, _x, _y, _label = ''):
        Event.__init__(self, _y)
        self.site = Site(_x, _y, _label)
        
    def __repr__(self):
        return "site event " + str(self.site)


class CircleEvent(Event):
    def __init__(self, _x, _y):
        self.p = Vector(_x, _y)
        Event.__init__(self, _y)

    def __repr__(self):
        return "circle event:   " + str(self.p)
        
        
def area(polygon):
    result = 0.0
    for i in range(len(polygon)):
        a = polygon[i]
        b = polygon[(i + 1) % len(polygon)]
        result += a.x * b.y - b.x * a.y
    return result * 0.5
def center(polygon):
    cx = 0.0
    cy = 0.0
    a6 = 6.0 * area(polygon)
    for i in range(len(polygon)):
        a = polygon[i]
        b = polygon[(i + 1) % len(polygon)]
        cx += (a.x + b.x) * (a.x * b.y - b.x * a.y)
        cy += (a.y + b.y) * (a.x * b.y - b.x * a.y)
    return Vector(cx / a6, cy / a6)
        
        
def drawPoints(svg, p, style = 'fill: #000'):
    for x in p:
        c = circle(x.x, x.y, 3)
        c.set_style(style)
        svg.addElement(c)


def drawPolygon(svg, p, style = 'fill: none; stroke: #000;'):
    c = polygon(' '.join([str(p[i].x) + ' ' + str(p[i].y) for i in range(len(p))]))
    c.set_style(style)
    svg.addElement(c)
        
        
def drawLine(svg, a, b):
    c = line(a.x, a.y, b.x, b.y)
    c.set_style('stroke: #000')
    svg.addElement(c)
    
    
def clipPolygon(polygon, p, n):
    newPolygon = []
    lastInFlag = None
    lastp = None
    for i in range(len(polygon) + 1):
        x = polygon[i % len(polygon)]
        outCode = (x - p) * n
        inFlag = (outCode > 0.0)
        if lastInFlag != None:
            if inFlag != lastInFlag:
                # find intersection!
                t = (n * (lastp - p)) / ((n * -1) * (x - lastp))
                intersection = lastp + (x - lastp) * t
                newPolygon.append(intersection)
            if inFlag:
                newPolygon.append(x)
        lastInFlag = inFlag
        lastp = x
    return newPolygon
        
        
def cheap_voronoi(svg, outline, p, draw = True):
    newp = []
    for ia, a in enumerate(p):
        # let's calculate the voronoi cell for point a!
        area = outline
        # now clip the outline with every midline
        for ib, b in enumerate(p):
            if ia == ib:
                continue
            c = (a + b) * 0.5
            v = a - b
            area = clipPolygon(area, c, v)
        if draw:
            drawPolygon(svg, area, 'fill: #cc0000; fill-opacity: 0.1; stroke: #cc0000;')
        newp.append(center(area))
    return newp
    
    
def beachSpanIntersection(a, b, sweepy):
    pby2 = b.site.y - sweepy
    if (pby2 == 0.0):
        return b.site.x
        
    plby2 = a.site.y - sweepy
    if (plby2 == 0.0):
        return a.site.x
        
    hl = a.site.x - b.site.x
    aby2 = 1.0 / pby2 - 1.0 / plby2
    bb = hl / plby2
    
    if (aby2 != 0):
        return (-bb + math.sqrt(bb * bb - 2.0 * aby2 * (hl * hl / (-2 * plby2) - a.site.y + plby2 / 2 + b.site.y - pby2 / 2))) / aby2 + b.site.x
    return (a.site.x + b.site.x) / 2
    

def insertBeachSpan(beachLine, span, sweepy):
    if len(beachLine) == 0:
        beachLine.append(span)
    else:
        l = 0
        r = len(beachLine) - 1
        while l < r:
            # binary search
            m = (r - l) // 2 + l
            mr = INF
            if m < len(beachLine) - 1:
                mr = beachSpanIntersection(beachLine[m], beachLine[m + 1], sweepy)
            if span.site.x < mr:
                r = m
            else:
                l = m + 1
        beachLine.insert(l + 1, beachLine[l])
        beachLine.insert(l + 1, span)
            
    return beachLine
    
    
def old_fortune(svg, outline, sites, draw = True):
    # fel: future event list
    fel = []
    
    beachLine = []
    
    # add points to future event list
    for site in sites:
        heapq.heappush(fel, [site.y, site, SITE_EVENT])
        
    # process future event list until it's empty
    while len(fel) > 0:
        item = heapq.heappop(fel)
        sweepy = item[0]
        #print(item)
        if item[2] == SITE_EVENT:
            # create a new beach span
            span = Struct()
            span.site = item[1]
            # insert beach span in the right place
            beachLine = insertBeachSpan(beachLine, span, sweepy)
            for i, span in enumerate(beachLine):
                xls = '-inf' if i == 0 else '%1.2f' % beachSpanIntersection(beachLine[i - 1], beachLine[i], sweepy)
                xrs = 'inf' if i == len(beachLine) - 1 else '%1.2f' % beachSpanIntersection(beachLine[i], beachLine[i + 1], sweepy)
                print(xls + ' to ' + xrs + ' / ' + str(span))
            print("")
            
            
def fortune(svg, outline, points, draw = False):
    futureEventList = []
    beachLine = BeachLine()
    
    for i, p in enumerate(points):
        heapq.heappush(futureEventList, SiteEvent(p.x, p.y, chr(65 + i)))

    while len(futureEventList) > 0:
        event = heapq.heappop(futureEventList)
        print(event)
        if isinstance(event, SiteEvent):
            beachLine.handleSiteEvent(event)
        else:
            beachLine.handleCircleEvent(event)
            
        print(beachLine)
        

if __name__ == '__main__': 
    svg = svg(width=str(WIDTH), height=str(HEIGHT))
    bg = rect(0, 0, WIDTH, HEIGHT)
    bg.set_style('fill: #fff')
    svg.addElement(bg)
    
    outline.append(Vector(120, 80))
    outline.append(Vector(300, 40))
    outline.append(Vector(480, 200))
    outline.append(Vector(350, 440))
    outline.append(Vector(130, 400))
    outline.append(Vector(60, 140))
    
    p = [Vector(random.random() * 200 + 150, random.random() * 200 + 150) for _ in range(N)]
    

    for _ in range(20):
        p = cheap_voronoi(svg, outline, p, draw = False)
        #drawPoints(svg, p, style='fill: #000; fill-opacity: ' + str(_ / 20.0))
    p = cheap_voronoi(svg, outline, p, draw = True)
    for _ in p:
        print(_.x, _.y)
    print('')
    
    fortune(svg, outline, p, draw = False)
    drawPoints(svg, p)
    drawPolygon(svg, outline)
    
    svg.save('out.svg')
