from blender_server.celery import app

import json
import socket
import requests
import os
import blender_server.config.environment as env
import sys
import time
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
		js = json.dumps(data)
		blend = openBlender(data["template"])
		time.sleep(2)
		response = connect(js, blend)
		blend.terminate()
		vids = convert(response["path"], data['render_type'], response["url"])
		onRenderSuccess(data, vids)
		
	except Exception as e:
		err = {'TASK-error': e}
		logger.error(err)
		return err

def openBlender(template):
	logger.error(env.TEMPLATES[template]["path"])

	blend_args = [env.BLENDER_EXEC, "-b", env.TEMPLATES[template]["path"], "-P", env.BLENDER_SCRIPT]
	blend = Popen(blend_args)
	return blend
	#stdout, stderr = blend.communicate()

def connect(json_send, blend):
	logger.error("ENTER CONNECTION")
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('127.0.0.1', 13373))
	logger.error("CONNECT SUCCESS")
	logger.error(json_send)
	s.send(json_send)
	logger.error("PASS SEND")
	#stdout, stderr = blend.communicate()
	response = json.loads(s.recv(1024))
	logger.error("PASS RESPONSE")
	logger.error(json.dumps(response))
	s.close()
	return response		

def onRenderSuccess(data, vids):
	client = requests.session()
	x = client.get(env.RENDER_SUCCESS_URL)  # sets cookie
	csrftoken = x.text
	
	
	send = dict(code=data['code'], render_type=data["render_type"], urls = json.dumps(vids) , csrfmiddlewaretoken=csrftoken)
	r = client.post(env.RENDER_SUCCESS_URL, data=send, headers=dict(Referer=env.RENDER_SUCCESS_URL))	

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



