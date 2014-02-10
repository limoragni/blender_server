import json
import pickle
import socket
import requests
import os
import blender_server.config.environment as env
import sys
import time
import redis
from .models import Render, Render_state

from blender_server.celery import app
from django.conf import settings
from subprocess import Popen, PIPE

import logging
logger = logging.getLogger(__name__)

@app.task
def sendToBlender(data):
	try:
		files = getFiles(data['media_data'], data['media_url'], data['code'])
		#override url de imagenes
		data['media_url'] = files
		data['image_number'] = env.TEMPLATES[data["template"]]["imgs"]
		js_data = pickle.dumps(data)
		saveData(js_data)
		blend = openBlender(data["template"])
		#time.sleep(2)
		#response = connect(js, blend)
		#blend.terminate()
		
		response = getResponse()
		vids = convert(response["path"], data['render_type'], response["url"])
		logger.error("TASKID: " + str(sendToBlender.request.id))
		onRenderSuccess(data, vids, sendToBlender.request.id)
	
	except Exception as e:
		name = sys.exc_info()[1]
		fileName = os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename)
		line = sys.exc_info()[2].tb_lineno
		err = "Error: " + str(e) + " on " + fileName + " line " + str(line)
		logger.error(err) 
		# import traceback, os.path
		# top = traceback.extract_stack()[-1]
		# err = str(e) + ', '.join([type(e).__name__, os.path.basename(top[0]), "line " + str(top[1])])
		# logger.error(err)
		# # err = {'TASK-error': str(e)}
		# # logger.error(err)
		# return err

def openBlender(template):
	blend_args = [env.BLENDER_EXEC, "-b", env.TEMPLATES[template]["path"], "-P", env.BLENDER_SCRIPT]
	blend = Popen(blend_args)
	blend.communicate()
	return blend
	#stdout, stderr = blend.communicate()

def saveData(data):
	red = redis.StrictRedis(host='localhost', port=6379, db=0)
	red.set("current_task", data)

def getResponse():
	red = redis.StrictRedis(host='localhost', port=6379, db=0)
	data = red.get("current_task_response")
	return json.loads(data)

# def connect(json_send, blend):
# 	logger.error("ENTER CONNECTION")
# 	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 	s.connect(('127.0.0.1', 13373))
# 	logger.error("CONNECT SUCCESS")
# 	logger.error(json_send)
# 	s.send(json_send)
# 	logger.error("PASS SEND")
# 	#stdout, stderr = blend.communicate()
# 	response = json.loads(s.recv(1024))
# 	logger.error("PASS RESPONSE")
# 	logger.error(json.dumps(response))
# 	s.close()
# 	return response		

def onRenderSuccess(data, vids, task_id):
	client = requests.session()
	x = client.get(env.RENDER_SUCCESS_URL)  # sets cookie
	csrftoken = x.text
	
	send = dict(code=data['code'], render_type=data["render_type"], urls = json.dumps(vids) , csrfmiddlewaretoken=csrftoken)
	r = client.post(env.RENDER_SUCCESS_URL, data=send, headers=dict(Referer=env.RENDER_SUCCESS_URL))
	rdb = Render.objects.get(task_id=task_id)
	rst = Render_state.objects.get(code=2)
	rdb.render_state = rst

def convert(path, render_type, response_url):
	if render_type == 'FINAL':
		quality = 'high'
	else:
		quality = 'low'
	##TODO:MOVER A OTRA TAREA!!
	
	# ffmpeg -i /path/ -y  -vcodec libvpx -f webm -preset veryslow -qp 0 -strict experimental path/out.webm
	#ffmpeg -i path/in -y -bt 1500k -vcodec libtheora -preset veryslow -qp 0 path/out.ogv
	#ffmpeg -i path/in -y -c:v  libx264 -preset veryslow -qp 0 -strict experimental path/out.mp4

	shell = {
	    'webm': {
	        'high': ['ffmpeg', '-i', path,'-y', '-vcodec', 'libvpx', '-f', 'webm','-preset', 'veryslow','-qp','0','-strict', 'experimental', os.path.splitext(path)[0]  + ".webm"] ,
	        'low':['ffmpeg', '-i', path,'-y', '-vcodec', 'libvpx', '-f', 'webm','-strict', 'experimental', os.path.splitext(path)[0]  + ".webm"] 
	    },
	    'ogv': {
	        'high':['ffmpeg', '-i', path,'-y', '-bt', '1500k', '-vcodec', 'libtheora', '-preset', 'veryslow','-qp','0',  os.path.splitext(path)[0]  + ".ogv"],
	        'low': ['ffmpeg', '-i', path,'-y', '-bt', '1500k', '-vcodec', 'libtheora', '-g', '30', '-s', '640x360',  os.path.splitext(path)[0]  + ".ogv"]
	    },
	    'mp4': {
	        'high': ['ffmpeg', '-i', path,'-y', '-c:v', 'libx264','-preset', 'veryslow','-qp','0', '-strict', 'experimental', os.path.splitext(path)[0]  + ".mp4"],
	        'low': ['ffmpeg', '-i', path,'-y', '-c:v', 'libx264', '-strict', 'experimental', os.path.splitext(path)[0]  + ".mp4"]
	    }
	}

	webm = Popen(shell['webm'][quality], stdout=PIPE)
	stdout, stderr = webm.communicate()

	mp4 = Popen(shell['mp4'][quality], stdout=PIPE)
	stdout, stderr = mp4.communicate()

	ogv = Popen(shell['ogv'][quality], stdout=PIPE)
	stdout, stderr = ogv.communicate()

	vids = {
		'mp4': os.path.splitext(response_url)[0]  + ".mp4",
		'webm': os.path.splitext(response_url)[0]  + ".webm",
		'ogg':  os.path.splitext(response_url)[0]  + ".ogv"
	} 
	return vids	

def download_file(frm, to):
	local_filename = frm.split('/')[-1]
	r = requests.get(frm, stream=True)
	if not os.path.exists(to):
		os.makedirs(to)
	with open(to + "/" + local_filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
				f.flush()
	return local_filename

def getFiles(flist, url, code):
	path = os.path.join(settings.TMP_ROOT, code)
	for f in flist:
		download_file(url + f, path)
	return path



