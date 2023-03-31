import argparse
import sys
import time
import subprocess as sp
import threading

import cv2
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
import numpy as np
import math
from trackeable import TrackableObject
from datetime import datetime
from upload import GoogleSheet
from functions import *
from dataFirebase import FireData

counter, fps = 0, 0
fps_avg_frame_count = 10
start_time = time.time()

cap = cv2.VideoCapture(0)#'TestVideo/TestVideo3.mp4')
width = 640#int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = 480#int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
#/home/cristian/Escritorio/Vision/models/firstModels/efficientnet_lite4.tflite
base_options = core.BaseOptions(file_name = 'models/firstModels/efficientdet_lite0.tflite')
detection_options = processor.DetectionOptions(max_results = 100, score_threshold = 0.3) ### cambiar
options = vision.ObjectDetectorOptions(base_options = base_options, detection_options = detection_options)
detector = vision.ObjectDetector.create_from_options(options)
    
centerPointsPrevFrame = []
trackingObjects = {}
trackId = 0

roi_position_entry = 0.5 #rigth
roi_position_exit = 0.5 #left

position = [0,0,0,0] #left, right, up, down;
trackableobject = {}
Eje = True # x = True, y = False

sheet = GoogleSheet()
sheet.ReadData()
#### ZOOM
scale = 50
x_offset = 0
y_offset = 0
cantZoom = 0

## ENCENDER STREAM
StreamOn = False
stream_log = False
proc = False
cmd = [
    'ffmpeg',
    #'-hide_banner',
    #'-stream_loop', '-1',
    #'-re',
    '-f','rawvideo',
    '-framerate','5',
    '-s','{}x{}'.format(width, height),
    '-pix_fmt', 'bgr24',
    '-i','-',
    '-g', '0',#'0',#'6,12,24,48',
    '-pix_fmt', 'yuv420p',
    '-c:v','libx264',
    '-preset','ultrafast',
    '-tune','zerolatency',
    '-f','flv',
    'rtmp://visionsinc.xyz/show/test'
    ]

#proc = sp.Popen(cmd, stdin = sp.PIPE)
## RESET VALUE STREAMING
FireData = FireData()
FireData.start()

pxl_entr = [470,560]
while True:
    if trackId > 100:
        trackId = 0
        trackableobject = {}
    
    StreamOn = FireData.Stream
    cantZoom = FireData.cantZoom
    x_offset = FireData.x_offset
    y_offset = FireData.y_offset
    Hora_Alerta = FireData.Hora  ## 10:30:00
    Hora_Actual = datetime.now().time()
    
    ret, frame = cap.read()
    
    #cv2.imshow('frame_original', frame)
    
    key = cv2.waitKey(1)
    
    if not ret:
        print('no file')
        break
    
    counter +=1
    objects = []
    centerPointsCurFrame = []
    
    #frame = cv2.flip(frame, 1)
    #frame = cv2.flip(frame, 0)
    frame = cv2.resize(frame, (width,height))    
    
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    input_tensor = vision.TensorImage.create_from_array(rgb_image)
    
    detection_result = detector.detect(input_tensor)
        
    for detection in detection_result.detections:
        category = detection.categories[0]
        category_name = category.category_name
        #score = detection.classes[0].score
        #category_name = detection.classes[0].class_name
        if category_name == 'person':
            '''if (Hora_Actual > Hora_Alerta and len(detection_result.detections) > 0):
                SendAlertStatus(True)
                alerStatus = True'''
            probability = round(category.score, 2)        
            bbox = detection.bounding_box
            #print(bbox)
            star_point = bbox.origin_x, bbox.origin_y
            end_point = bbox.origin_x + bbox.width, bbox.origin_y + bbox.height
            cv2.rectangle(frame, star_point, end_point, (0,255,0), 2)
            
            result_text = category_name + '('+str(round(probability*100))+'%)'
            text_location = (bbox.origin_x + 10, -10 + bbox.origin_y)
            
            cv2.putText(frame, result_text, text_location, cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)
            
            xmin = star_point[0]
            xmax = end_point[0]
            ymin = star_point[1]
            ymax = end_point[1]
            xcenter = xmin + (int(round((xmax - xmin )/ 2)))
            ycenter = ymin + (int(round((ymax - ymin )/ 2)))
            #cv2.circle(frame, (xcenter, ycenter), 5, (0,255,0), -1)
            centerPointsCurFrame.append((xcenter, ycenter))
            objects.append((xmin,ymin,xmax,ymax))
            
    if counter <= 1:        
        for pt in centerPointsCurFrame:
            for pt2 in centerPointsPrevFrame:
                distance = math.hypot(pt2[0] - pt[0], pt2[1]-pt[1])
                
                if distance < 10:
                    trackingObjects[trackId] = pt
                    trackId += 1
    else:
        trackingObjects_copy = trackingObjects.copy()
        centerPointsCurFrame_copy = centerPointsCurFrame.copy()
        for objectId, pt2 in trackingObjects_copy.items():
            object_exists = False
            for pt in centerPointsCurFrame_copy:
                distance = math.hypot(pt2[0] - pt[0], pt2[1]-pt[1])
                if distance < 20:
                    trackingObjects[objectId] = pt
                    object_exists = True
                    if pt in centerPointsCurFrame:
                        centerPointsCurFrame.remove(pt)
                    continue
                
            if not object_exists:
                trackingObjects.pop(objectId)
    
    for pt in centerPointsCurFrame:
        trackingObjects[trackId] = pt
        trackId +=1
    
    counted = False
    
    for objectId, pt in trackingObjects.items():
        
        to = trackableobject.get(objectId, None)
        
        if to is None:
            to = TrackableObject(objectId, pt)
        else:
            '''
            if not to.countedEntry:
                Ypos = [c[1] for c in to.centroids]
                direction = pt[1] - np.mean(Ypos)
                linePoint = roi_position_entry * height
                
                if (pt[1] > linePoint and direction > 0 and pxl_entr[0] <= pt[0] <= pxl_entr[1]
                    and not to.countedEntry and linePoint-10 < pt[1] < linePoint +10):
                    position[3] += 1
                    to.countedEntry = True
                    date = datetime.now().strftime('%d/%m/%Y')
                    now = datetime.now().strftime('%H:%M:%S')
                    sheet.sendData(date,'Entry', now)
                    sheet.Entry += 1
                    
                if (pt[1] < linePoint and direction < 0 and pxl_entr[0] <= pt[0] <= pxl_entr[1]
                    and not to.countedExit and linePoint-10 < pt[1] < linePoint +10):
                    position[0] += 1
                    to.countedExit = True
                    date = datetime.now().strftime('%d/%m/%Y')
                    now = datetime.now().strftime('%H:%M:%S')
                    sheet.sendData(date,'Exit', now)
                    sheet.Exit += 1
                    
            '''
            if not to.countedEntry:
                Xpos = [c[0] for c in to.centroids]
                direction = pt[0] - np.mean(Xpos)
                linePoint = roi_position_entry * height
                
                if pt[0] > roi_position_entry*width and direction > 0 and np.mean(Xpos) < roi_position_entry*width:
                    position[1] += 1
                    to.countedEntry = True
                    date = datetime.now().strftime('%d-%m-%Y')
                    now = datetime.now().strftime('%H:%M:%S')
                    sheet.sendData(date,'Entry', now)
                    sheet.Entry += 1
                    
            if not to.countedExit:
                #if pt[0] < roi_position_exit*width and direction < 0 and np.mean(Xpos) > roi_position_exit*width:    
                if pt[0] < roi_position_entry*width and direction < 0 and np.mean(Xpos) > roi_position_entry*width:
                    position[0] += 1
                    to.countedExit = True
                    date = datetime.now().strftime('%d-%m-%Y')
                    now = datetime.now().strftime('%H:%M:%S')
                    sheet.sendData(date,'Exit', now)
                    sheet.Exit += 1
                    
            to.centroids.append(pt)
        trackableobject[objectId] = to
        
        cv2.circle(frame, pt, 3, (0,255,0), -1)
        cv2.putText(frame, str(objectId), (pt[0], pt[1] - 7),0, 1, (0, 0, 255), 2)
    
    if counter % fps_avg_frame_count == 0:
        end_time = time.time()
        fps = fps_avg_frame_count / (end_time - start_time)
        start_time = time.time()
        
    fps_text = 'FPS = {:.1f}'.format(fps)
    cv2.putText(frame, fps_text, (24,20), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255), 1)
    #cv2.line(frame, (pxl_entr[0],  int(roi_position_entry*height)), (pxl_entr[1], int(roi_position_entry*height)),(0xFF,0,0),2)
    cv2.line(frame, (int(roi_position_entry*width), 0),(int(roi_position_entry*width), height), (0xFF,0,0),2)
    #cv2.line(frame, (int(roi_position_exit*width), 0),(int(roi_position_exit*width), height), (0, 0, 255), 5)
    cv2.putText(frame, f'Entrada:{sheet.Entry}; Salida: {sheet.Exit}',(10,15), 1,1, (255, 255, 255), 2, cv2.FONT_HERSHEY_SIMPLEX )        
    
    centerPointsPrevFrame = centerPointsCurFrame.copy()

    if key == 27:
        break
    
    scale, cantZoom= ZoomKey(cantZoom)
    scale, cantZoom, x_offset, y_offset = StatusZoom(scale, cantZoom,x_offset,y_offset)
    frame  = DisplayZoom(frame, scale, x_offset, y_offset, width, height)
    #frame_out = cv2.resize(frame, (1280,720))
    cv2.imshow('frame', frame)
    
    if StreamOn == True:
        try:
            if not stream_log:
                print("Stream On")
            proc.stdin.write(frame.tobytes())
            stream_log = True
        except Exception as e:
            proc = sp.Popen(cmd, stdin = sp.PIPE)
    else:
        if stream_log == True:
            proc.terminate()
            print('Stream Off')
            stream_log = False
    time.sleep(1/1000)
            
if proc is not False:
    proc.terminate()
cap.release()
cv2.destroyAllWindows()
FireData.stop()



