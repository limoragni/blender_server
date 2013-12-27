import socketserver
import json
import bpy
import os
import sys

blend_dir = os.path.dirname(os.path.abspath(__file__))
if blend_dir not in sys.path:
   sys.path.append(blend_dir)

import config as conf

class Renderer():
    
    renderData = {}
    
    def render(self, data):
        self.processJSON(data)
        self.setTemplate(self.renderData['template'], self.renderData['render_type'])
        #imgs_source = ["ozymandias01.jpg.001", "mononoke.jpg", "pacific-rim.jpg"]S
        imgs_remote = self.renderData['media_data']
        imgs_directory = self.renderData["media_url"]
        
        for i,v in enumerate(imgs_remote):
            bpy.data.images["imagen0" + str(i + 1)].filepath = imgs_directory + "/" + v

        bpy.data.scenes["Scene"].render.filepath = os.path.join(conf.RENDER_PATH, self.renderData["code"] + "_" + self.renderData["render_type"] + '#')
        bpy.ops.render.render(animation=True);
        response = {'path': self.getRenderFilePath(), 'url': self.getRenderURL() }
        return response

    def processJSON(self, data):
        self.renderData = data

    def getFilename(self):
        fs = bpy.data.scenes["Scene"].frame_start
        fe = bpy.data.scenes["Scene"].frame_end
        c = self.renderData["code"] + "_" + self.renderData["render_type"]
        return c + str(fs) + '-' + str(fe) + conf.CONTAINER

    def getRenderURL(self):
        return os.path.join(conf.RENDER_URL, self.getFilename())

    def getRenderFilePath(self):
        return os.path.join(conf.RENDER_PATH, self.getFilename())
    
    def setTemplate(self, name, render_type):
        #bpy.ops.wm.open_mainfile(filepath= '/home/limoragni/Dev/djangoapps/blender_server/blender/templates/template-hand/testing02-03_hand.blend')
        if render_type == "FINAL":
            quality = 60
        else:
            quality = 40
        bpy.data.scenes["Scene"].render.resolution_percentage = quality

class MyTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(1024).decode('UTF-8').strip()
            loaded_data = json.loads(data)
            r = Renderer()
            response = r.render(loaded_data)
            self.request.sendall(bytes(json.dumps(response), 'UTF-8'))
            bpy.ops.wm.quit_blender()
        except Exception as e:
            self.request.sendall(bytes(json.dumps({'BLEND_SERVER_ERROR':"ERROR"}), 'UTF-8'))
            

server = MyTCPServer(('127.0.0.1', 13373), MyTCPServerHandler)
server.serve_forever()
