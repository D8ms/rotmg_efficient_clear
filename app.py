from tkinter import Tk, Canvas, NW, CENTER, Button, Label, Text
from PIL import Image, ImageFilter, ImageTk
import cv2
import numpy
from math import sqrt, ceil
import requests
import json
import configparser
from mss import mss
import time
from pubsub import pub
import threading
import os
import sys


class AppConfig:
    def __init__(self, configName):
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        elif __file__:
            self.app_path = os.path.dirname(__file__)
        _config = configparser.ConfigParser()
        _config.read(os.path.join(self.app_path, configName))
        config = _config['Application']
        self.gui_width = int(config['GUI_WIDTH'])
        self.gui_height = int(config['GUI_HEIGHT'])
        self.gui_refresh_rate = int(config['GUI_REFRESH_RATE'])
        
        config = _config['Network']
        self.use_network = config['USE_NETWORK'].lower().strip() == 'true'
        self.server_url = config['SERVER_URL']
        self.network_refresh_rate = int(config['NETWORK_REFRESH_RATE'])
        self.room = config['ROOM']
        
        config = _config['Overlay']
        self.use_overlay = config['USE_OVERLAY'].lower().strip() == 'true'
        self.overlay_refresh_rate = int(config['OVERLAY_REFRESH_RATE'])
        self.minimap_width = int(config['MINIMAP_WIDTH'])
        self.minimap_height = int(config['MINIMAP_HEIGHT'])
        self.map_width = int(config['MAP_WIDTH'])
        self.map_height = int(config['MAP_HEIGHT'])
        self.map_x = int(config['MAP_X'])
        self.map_y = int(config['MAP_Y'])
        self.alpha = int(config['ALPHA'])

        
class MYGUI:
    def __init__(self, config, sct):
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        elif __file__:
            self.app_path = os.path.dirname(__file__)
        self.config = config
        self.root = Tk()
        self.root.geometry(str(config.gui_width) + "x" + str(config.gui_height))
        self.sct = sct
     
        self.gui_width = config.gui_width
        self.gui_height = config.gui_height
        self.canvas = Canvas(self.root, width=self.gui_width, height=self.gui_height)
        self.canvas.pack()
        self.init_maps_pis()
        self.mapLayer = self.canvas.create_image(0, 0, anchor=NW, image=self.mapPIs[0])
        self.init_markers()
        self.draw_markers()
        
        self.protected_markers = {}
        self.protection_time = 1 #1 second
    
        self.use_network = self.config.use_network
        if self.use_network:
            self.endpoint = self.config.server_url + '/' + self.config.room
            self.server = "..."
            self.n_cd = 0
            pub.subscribe(self.fullSync, "FullSync")
            pub.subscribe(self.partialSync, "PartialSync")
        
        self.use_overlay = self.config.use_overlay
        if self.use_overlay:
            self.minimap_area = {
                "top": self.config.map_y,
                "left": self.config.map_x,
                "width": self.config.minimap_width,
                "height": self.config.minimap_height
            }
            self.alpha = self.config.alpha
            self.overlayLayer = None
            self.g_cd = 0
        
        self.root.bind("<Button 1>", self.left_click)
        self.root.bind("<Button 3>", self.right_click)
        self.root.bind("<Right>", self.next_map)
        self.root.bind("<Left>", self.prev_map)
        self.root.bind("<Key>", self.process_key_press)
        
        self.estimate_text = "Marked Heroes: 0 "
        self.heroEstimateLabel = Label(self.root, bg="black", fg="#03fc62", font=("Arial", 25), text=self.estimate_text)
        self.heroEstimateLabel.place(relx=0.5, rely=0.02, anchor='center')
        
        self.running = not (self.use_network or self.use_overlay)
        self.pause_text = "PAUSED"
        self.pauseLabel = Label(self.root, font=("Arial", 50), text=self.pause_text)
        if not self.running:
            self.pauseLabel.place(relx=0.5, rely=0.5, anchor='center')
            self.root.bind("<space>", self.toggle_pause)
            self.update_clock()
        self.root.mainloop()
        
    def toggle_pause(self, e):
        if self.running:
            self.pauseLabel.place(relx=0.5, rely=0.5, anchor='center')
            self.running = False
        else:
            self.pauseLabel.place_forget()
            self.running = True
            self.update_clock()
            
        
    def init_markers(self):
        widthRatio = self.gui_width / self.config.map_width
        heightRatio = self.gui_height / self.config.map_height
        markerWidth = int(widthRatio * 36)
        markerHeight = int(heightRatio * 36)
        self.marker_activation_radius = (markerWidth + markerHeight) / 4
        mapCoord_path = os.path.join(self.app_path, 'mapCoords/')
        whitePi = ImageTk.PhotoImage(Image.open(mapCoord_path + 'whitemark.png').resize((markerWidth, markerHeight)))
        greenPi = ImageTk.PhotoImage(Image.open(mapCoord_path + 'greenmark.png').resize((markerWidth, markerHeight)))
        redPi = ImageTk.PhotoImage(Image.open(mapCoord_path + 'redmark.png').resize((markerWidth, markerHeight)))
        self.markerPIs = [whitePi, greenPi, redPi]
        self.mapToMarkerCoords = []
        self.markerPiIdxs = [0] * 128
        self.markers = []
        for i in range(13):
            coordPath = mapCoord_path + "map" + str(i+1) + ".txt"
            with open(coordPath) as fh:
                coordData = []
                for line in fh:
                    x, y = line.strip().split(', ')
                    x = int(int(x) * widthRatio)
                    y = int(int(y) * heightRatio)
                    coordData.append((x, y))
                self.mapToMarkerCoords.append(coordData)
                
    def clear_markers(self):
        self.protected_markers = {}
        for marker in self.markers:
            self.canvas.delete(marker)
        self.markers.clear()
        self.markerPiIdxs = [0] * 128
    
    def draw_markers(self):
        coords = self.mapToMarkerCoords[self.mapIdx]
        for c in coords:
            x, y = c
            self.markers.append(self.canvas.create_image(x, y, anchor=CENTER, image=self.markerPIs[0]))
            
        widthRatio = self.gui_width / self.config.map_width
        heightRatio = self.gui_height / self.config.map_height
        x = widthRatio * 0.9 * self.config.map_width
        y = heightRatio * 0.9 * self.config.map_height
        self.syncMarker = self.canvas.create_image(x, y, anchor=CENTER, image=self.markerPIs[0])
        
    def overlay(self, image):
        self.overlayImage = self.preprocess_map(image)
        if self.overlayLayer:
            self.canvas.itemconfig(self.overlayLayer, image=self.overlayImage)
        else:
            self.overlayLayer = self.canvas.create_image(0,0, anchor=NW, image=self.overlayImage)
        
    def preprocess_map(self, image):
        resized = cv2.resize(image, (self.gui_width, self.gui_height))
        return ImageTk.PhotoImage(Image.fromarray(resized))
        
    def tick_network(self):
        if not self.use_network:
            return False
        if self.n_cd > 0:
            self.n_cd -= self.config.gui_refresh_rate
        else:
            self.n_cd = self.config.network_refresh_rate
        return self.n_cd <= 0
            
    def tick_gui(self):
        if not self.use_overlay:
            return False
        if self.g_cd > 0:
            self.g_cd -= self.config.gui_refresh_rate
        else:
            self.g_cd = self.config.overlay_refresh_rate
        return self.g_cd <= 0
        
    def update_clock(self):
        if not self.running:
            return
        if self.tick_network():
            self.partialCommunicator = Communicator(self.endpoint, queue="PartialSync")
            self.partialCommunicator.start()
        if self.tick_gui():
            img = self.sct.grab(self.minimap_area)
            img = numpy.array(self.sct.grab(self.minimap_area))
            b, g, r, a = cv2.split(img)
            a -= (255 - self.alpha)
            self.overlay(cv2.merge((r, g, b, a)))
        self.root.after(self.config.gui_refresh_rate, self.update_clock)
    
    def update_hero_estimate(self):
        est = 0
        for i in self.markerPiIdxs:
            if i > 0:
                est += 1
        est = str(est)
        if len(est) < 2:
            est += " "
            
        self.estimate_text = "Marked Heroes: " + est
        self.heroEstimateLabel.config(text=self.estimate_text)
        
    def init_maps_pis(self):
        self.baseMap = None
        self.mapPIs = []
        self.mapIdx = 0
        for i in range(13):
            idx = i + 1
            location = os.path.join(self.app_path, "MAPS/" + "map" + str(idx) + ".png")
            map = Image.open(location)
            smaller_map = map.resize((self.gui_width, self.gui_height))
            pi = ImageTk.PhotoImage(smaller_map)
            self.mapPIs.append(pi)
    
    def next_map(self, event):
        self.set_map((self.mapIdx + 1) % 13)
        self.update_hero_estimate()
        
    def prev_map(self, event):
        self.set_map((self.mapIdx - 1) % 13)
        self.update_hero_estimate()
        
    def set_map(self, mapIdx):
        if self.mapIdx == mapIdx:
            return
        else:
            self.mapIdx = mapIdx
            self.canvas.itemconfig(self.mapLayer, image=self.mapPIs[self.mapIdx])
            self.reset_markers()
            
    def reset_markers(self):
        self.clear_markers()
        self.draw_markers()
        
    def process_key_press(self, event):
        if not self.use_network:
            return
        key = event.char
        if key in ["s", "S"]:
            self.fullSyncComm = Communicator(self.endpoint, queue="FullSync")
            self.fullSyncComm.start()
        if key in ["u", "U"]:
            self.uploadAllData()
        
    def left_click(self, event):
        c = (event.x, event.y)
        circleId = self.maybe_get_closest_circle_id(c)
        if circleId >= 0:
            self.protected_markers[circleId] = time.time()
            if self.markerPiIdxs[circleId] != 1:
                newCirclePiId = 1
            else:
                newCirclePiId = 0
            self.markerPiIdxs[circleId] = newCirclePiId
            circlePI = self.markerPIs[newCirclePiId]
            self.canvas.itemconfig(self.markers[circleId], image=circlePI)
            if self.use_network:
                self.uploadMarker(circleId, newCirclePiId)
        self.update_hero_estimate()   
         
        
    def right_click(self, event):
        c = (event.x, event.y)
        circleId = self.maybe_get_closest_circle_id(c)
        if circleId >= 0:
            self.protected_markers[circleId] = time.time()
            if self.markerPiIdxs[circleId] != -1:
                newCirclePiId = -1
            else:
                newCirclePiId = 0
            self.markerPiIdxs[circleId] = newCirclePiId
            circlePI = self.markerPIs[newCirclePiId]
            self.canvas.itemconfig(self.markers[circleId], image=circlePI)
            if self.use_network:
                self.uploadMarker(circleId, newCirclePiId)
        self.update_hero_estimate()
        
    def least_distance(self, c):
        bestDistance = 100000000000
        bestIdx = 128
        markerCoords = self.mapToMarkerCoords[self.mapIdx]
        for i in range(len(markerCoords)):
            coord = markerCoords[i]
            d = self.dist(coord, c)
            if d < bestDistance:
                bestIdx = i
                bestDistance = d
        return (bestIdx, bestDistance)
        
    def maybe_get_closest_circle_id(self, c):
        circleIdx, dst = self.least_distance(c)
        if dst < self.marker_activation_radius:
            return circleIdx
        return -1
        
    def dist(self, a, b):
        return sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def accounted_rems(self):
        ret = 0
        for i in self.markerPiIdxs:
            if i > 1:
                ret += 1
        return ret
       
    def downloadMarkerPiIdxs(self):
        pass                
    
    def resetServerMarkers(self):
       d = {'reset': 1}
       self.post(d)
        
    def uploadMarker(self, markerId, markerPiIdx):
        data = {
            "mapIdx": str(self.mapIdx),
            "server": str(self.server),
            str(markerId): str(markerPiIdx)
        }
        self.markerWorker = Communicator(self.endpoint, data=data)
        self.markerWorker.start()
        
    def uploadAllData(self):
        data = {}
        for i in range(128):
            data[str(i)] = str(self.markerPiIdxs[i])
        data['mapIdx'] = str(self.mapIdx)
        data['server'] = str(self.server) #TODO
        self.uploadFullSyncComm = Communicator(self.endpoint, data=data, post=True)
        self.uploadFullSyncComm.start()
        
    def downloadFull(self):
        response = requests.get(self.endpoint)
        if response.ok:
            return response.json()
        else:
            print("could not retrieve full info from server", response.reason)
    
    def fullSync(self, data):
        self.protected_markers = {}
        self.server = data['server']
        self.set_map(int(data['mapIdx']))
        serverMarkerPiIdxs = data['markerPiIdxs']
        self.updateMarkers(serverMarkerPiIdxs)
        self.update_hero_estimate()
    
    def partialSync(self, data):
        serverMapIdx = int(data['mapIdx'])
        self.server = data['server']
        if self.updateMapSyncSignal(serverMapIdx):
            serverMarkerPiIdxs = data['markerPiIdxs']
            self.updateMarkers(serverMarkerPiIdxs)
            self.update_hero_estimate()
        
        #data should only sync if you are on the same map as the server
    def updateMapSyncSignal(self, serverMapIdx):
        circlePiIdx = -1
        if serverMapIdx == self.mapIdx:
            circlePiIdx = 1
        self.canvas.itemconfig(self.syncMarker, image=self.markerPIs[circlePiIdx]) 
        return circlePiIdx == 1
        
    def updateMarkers(self, newMarkersPiIdxs):
        cur_time = time.time()
        for i in range(128):
            if i in self.protected_markers.keys():
                toggled_time = self.protected_markers[i]
                if cur_time - toggled_time < self.protection_time:
                    continue
                else:
                    del self.protected_markers[i]
            newMarkerPiIdx = int(newMarkersPiIdxs[i])
            if self.markerPiIdxs[i] != newMarkerPiIdx:
                self.markerPiIdxs[i] = newMarkerPiIdx
                circlePI = self.markerPIs[newMarkerPiIdx]
                self.canvas.itemconfig(self.markers[i], image=circlePI)
    
class ReadWorker(threading.Thread):
    def __init__(self, endpoint, data):
        super(Communicator, self).__init__()
        self.daemon = True
        self._stop = False    
        self.endpoint = endpoint  

    def run(self):
        response = requests.get(self.endpoint)
        if response.ok:
            pub.sendMessage("fullListener", data=response.json())
        else:
            print("could not retrieve full info from server", response.reason)
        
class Communicator(threading.Thread):
    def __init__(self, endpoint, queue=None, data=None, post=False):
        super(Communicator, self).__init__()
        self.daemon = True
        self._stop = False    
        self.queue = queue
        self.endpoint = endpoint
        self.data = data
        self.post = post
        
    def run(self):
        if self.queue:
            self.getFull(self.queue)
        if self.data:
            self.sendData(self.data)
        
    def getFull(self, queue):
        response = requests.get(self.endpoint)
        if response.ok:
            pub.sendMessage(queue, data=response.json())
        else:
            print("could not retrieve full info from server", response.reason)
       
    def sendData(self, data):
        if self.post:
            res = requests.post(self.endpoint, json=data)
        else:
            res = requests.put(self.endpoint, json=data)
        if not res.ok:
            print("Uploading failed", res.reason)
            
if __name__ == '__main__':
    with mss() as sct:
        config = AppConfig('config.ini')
        gui = MYGUI(config, sct)
            
