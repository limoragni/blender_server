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
        
        imgs_source = ["ozymandias01.jpg.001", "mononoke.jpg", "pacific-rim.jpg"]
        imgs_remote = self.renderData['media_data']
        imgs_directory = self.renderData["media_url"]
        for i, v in enumerate(imgs_source):
            print(imgs_directory + imgs_remote[i])
            bpy.data.images[v].filepath = imgs_directory + "/" + imgs_remote[i]

        bpy.data.scenes["Scene"].render.filepath = os.path.join(conf.RENDER_PATH, self.renderData["code"] + '#')
        bpy.ops.render.render(animation=True);
        print(self.getRenderURL())
        return self.getRenderURL()

    def processJSON(self, data):
        self.renderData = json.loads(data)

    def getFilename(self):
        fs = bpy.data.scenes["Scene"].frame_start
        fe = bpy.data.scenes["Scene"].frame_end
        c = self.renderData["code"]
        return c + str(fs) + '-' + str(fe) + conf.CONTAINER

    def getRenderURL(self):
        return os.path.join(conf.RENDER_URL, self.getFilename())
        
class MyTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(1024).decode('UTF-8').strip()
            r = Renderer()
            response = r.render(data)
            self.request.sendall(bytes(json.dumps({'url': response}), 'UTF-8'))
        except Exception as e:
            self.request.sendall(bytes(json.dumps({'error':e}), 'UTF-8'))
            

server = MyTCPServer(('127.0.0.1', 13373), MyTCPServerHandler)
server.serve_forever()