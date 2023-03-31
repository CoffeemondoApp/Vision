import cv2
import time
from threading import Thread

def maxZoom(cantZoom):
    maxX = (((cantZoom * 5) * 2) * 3)
    maxY = ((cantZoom * 5) * 5)
    return maxX,-maxX, maxY, -maxY

def ZoomKey(cantZoom):
    scale = 50 - (5 * cantZoom)

    if scale <= 5:
        scale = 5
 
    elif scale >=50:
        scale = 50
    
    return(scale, cantZoom)

def StatusZoom(scale, cantZoom,x_offset,y_offset):
    if scale <= 5:
        scale = 5
    elif scale >= 50:
        scale = 50


    max_width_zoom, min_widt_zoom, max_height_zoom, min_height_zoom = maxZoom(cantZoom)

    if x_offset >  max_width_zoom:
        x_offset = max_width_zoom
    elif x_offset < min_widt_zoom:
        x_offset = min_widt_zoom

    if y_offset >=  max_height_zoom:
        y_offset = max_height_zoom
    elif y_offset <= min_height_zoom:
        y_offset = min_height_zoom
        
    return scale, cantZoom, x_offset,y_offset

def DisplayZoom(frame, scale, x_offset, y_offset, width, height):
    centerX,centerY=int(height/2),int(width/2)
    radiusX,radiusY= int(scale*height/100),int(scale*width/100)

    minX,maxX=centerX-radiusX+y_offset,centerX+radiusX+y_offset
    minY,maxY=centerY-radiusY+x_offset,centerY+radiusY+x_offset

    if minX < 0:
        minX = 0
    if minY < 0:
        minY = 0
    if maxX > height:
        maxX = height
    if maxY > width:
        maxY = width

    cropped = frame[minX:maxX, minY:maxY]
    resized_cropped = cv2.resize(cropped, (width, height))

    return resized_cropped


class SendAlert(Thread):
    def __init__(self):
        self.status = True
        self.time = 60 * 5
        super().__init__()
    def run(self):
        while self.status:
            self.timer()
            time.sleep(300)
    def stop(self):
        self.status = False
        
class sendAlertTime(SendAlert):
    def timer(self):
        print('send Alert')
        
def SendAlertStatus(Value):
    send = sendAlertTime()
    if Value:
        send.start()
    else:
        send.stop()
        
    