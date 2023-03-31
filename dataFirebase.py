import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from threading import Thread
from datetime import datetime
import time

class FireData(Thread):
    def __init__(self):
        Thread.__init__(self)
        cred = credentials.Certificate("Auth/credFire.json")

        firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://coffeemondo-365813-default-rtdb.firebaseio.com/'
        })
        self.Stream = False
        self.x_offset = 0
        self.y_offset = 0
        self.cantZoom = 0
        self.status = True
        self.Hora = datetime.strptime('23:59:59', "%X").time()
        
    def run(self):
        while self.status:
            try:
                data = db.reference('live').get()
                self.Stream = data['Streaming']
                self.x_offset = data['zoomInput']['inputLR']
                self.y_offset = data['zoomInput']['inputTB']
                self.cantZoom = data['zoomInput']['zoom']
                self.Hora = datetime.strptime(data['Hora'], "%X").time()
                #time.sleep(1/1000)
            except Exception as e:
                print(e)
                
    def stop(self):
        self.status = False