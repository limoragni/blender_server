import socketserver
import pickle
import json
import bpy
import os
import sys


blend_dir = os.path.dirname(os.path.abspath(__file__))
if blend_dir not in sys.path:
   sys.path.append(blend_dir)

import config as conf

sys.path.append('/opt/python3.3/lib/python3.3/site-packages/') 
import redis

def execAll():
    data = getData()
    setImages(data)
    setText(data)
    response = renderVideo(data)
    saveResponse(response)

def getData():
    red = redis.StrictRedis(host='localhost', port=6379, db=0)
    data = red.get("current_task")
    red.set('test', data)
    json_data = pickle.loads(data)
    return json_data

def setImages(data):
    imgs_remote = data['media_data']
    imgs_directory = data["media_url"]
    for i,v in enumerate(imgs_remote):
        bpy.data.images["imagen0" + str(i + 1)].filepath = imgs_directory + "/" + v

def setText(data):
    for i,v in enumerate(data['texts']):
        bpy.context.scene.objects.active = bpy.data.objects["Text.00" + str(i + 1)]
        bpy.ops.object.editmode_toggle()
        bpy.ops.font.delete()
        bpy.ops.font.text_insert(text=str(v))
        bpy.ops.object.editmode_toggle()

def renderVideo(data):
    bpy.data.scenes["Scene"].render.filepath = os.path.join(conf.RENDER_PATH, data["code"] + "_" + data["render_type"] + '#')
    bpy.ops.render.render(animation=True);
    response = {'path': getRenderFilePath(data), 'url': getRenderURL(data) }
    return response

def saveResponse(response):
    red = redis.StrictRedis(host='localhost', port=6379, db=0)
    data = red.set("current_task_response", json.dumps(response))
    bpy.ops.wm.quit_blender()

def getFilename(data):
    fs = bpy.data.scenes["Scene"].frame_start
    fe = bpy.data.scenes["Scene"].frame_end
    c = data["code"] + "_" + data["render_type"]
    return c + str(fs) + '-' + str(fe) + conf.CONTAINER

def getRenderURL(data):
    return os.path.join(conf.RENDER_URL, getFilename(data))

def getRenderFilePath(data):
    return os.path.join(conf.RENDER_PATH, getFilename(data))

execAll()
