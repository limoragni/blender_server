import socketserver
import json
import bpy
import os

RENDER_PATH = '/home/limoragni/Dev/djangoapps/blender_server/blender_server/media/renders/'
RENDER_URL = 'http://127.0.0.1:8444/media/renders/'
CONTAINER = '.ogv'

class Renderer():
    
    renderData = {}
    
    def render(self, data):
        self.processJSON(data)
        for i,v in enumerate(self.renderData['media_data']):
            bpy.data.scenes["Scene"].sequence_editor.sequences_all["img_" + str(i)].directory = self.renderData["media_url"]
            bpy.data.scenes["Scene"].sequence_editor.sequences["img_" + str(i)].strip_elem_from_frame(0).filename = v
        
        bpy.data.scenes["Scene"].render.filepath = os.path.join(RENDER_PATH, self.renderData["code"] + '#')
        bpy.ops.render.render(animation=True);
        
        return self.getRenderURL()

    def processJSON(self, data):
        self.renderData = json.loads(data)

    def getFilename(self):
        fs = bpy.data.scenes["Scene"].frame_start
        fe = bpy.data.scenes["Scene"].frame_end
        c = self.renderData["code"]
        return c + str(fs) + '-' + str(fe) + CONTAINER

    def getRenderURL(self):
        return os.path.join(RENDER_URL, self.getFilename())
        
class MyTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(1024).decode('UTF-8').strip()
            r = Renderer()
            response = r.render(data)
            self.request.sendall(bytes(json.dumps({'response': response}), 'UTF-8'))
        except Exception as e:
            self.request.sendall(bytes(json.dumps({'error':e}), 'UTF-8'))
            

server = MyTCPServer(('127.0.0.1', 13373), MyTCPServerHandler)
server.serve_forever()