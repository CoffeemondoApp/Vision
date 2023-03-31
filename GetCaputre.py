import cv2
import time
import os

cap = cv2.VideoCapture(0)
number_img = 300
savePath = './picturesTrain'
lenpath = len(os.listdir(savePath))

while True:
    for imgnum in range (number_img):
        print('Collecting image {}'.format(lenpath+imgnum))
        ret, frame = cap.read()
        frame = cv2.resize(frame, (640, 480))
        cv2.imshow('frame', frame)
        imgname = os.path.join(savePath, 'image_{}.jpg'.format(lenpath+imgnum))
        cv2.imwrite(imgname, frame)
        time.sleep(3)
    
    break

cap.release()
cv2.destroyAllWindows()