from blender_server.celery import app

import json
import socket
import requests
import os
import blender_server.config.environment as env
import sys
from django.conf import settings

from subprocess import Popen, PIPE

import logging
logger = logging.getLogger(__name__)

@app.task
def sendToBlender(data):
	try:
		files = getFiles(data['media_data'], data['media_url'], data['code'])
		logger.error(data['media_url'])
		#override url de imagenes
		data['media_url'] = files
		js = json.dumps(data)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('127.0.0.1', 13373))
		s.send(js)
		response = json.loads(s.recv(1024))
		s.close()
		
		if data['render_type'] == 'FINAL':
			quality = 'high'
		else:
			quality = 'low'
		##TODO:MOVER A OTRA TAREA!!
		shell = {
			'webm': {
				'high': ['ffmpeg', '-i', response["path"],'-y', '-vcodec', 'libvpx', '-f', 'webm','-preset', 'veryslow','-qp','0','-strict', 'experimental', os.path.splitext(response["path"])[0]  + ".webm"] ,
				'low':['ffmpeg', '-i', response["path"],'-y', '-vcodec', 'libvpx', '-f', 'webm','-strict', 'experimental', os.path.splitext(response["path"])[0]  + ".webm"] 
			},
			'ogv': {
				'high':['ffmpeg', '-i', response["path"],'-y', '-bt', '1500k', '-vcodec', 'libtheora', '-preset', 'veryslow','-qp','0',  os.path.splitext(response["path"])[0]  + ".ogv"],
				'low': ['ffmpeg', '-i', response["path"],'-y', '-bt', '1500k', '-vcodec', 'libtheora', '-g', '30', '-s', '640x360',  os.path.splitext(response["path"])[0]  + ".ogv"]
			},
			'mp4': {
				'high': ['ffmpeg', '-i', response["path"],'-y', '-c:v', 'libx264','-preset', 'veryslow','-qp','0', '-strict', 'experimental', os.path.splitext(response["path"])[0]  + ".mp4"],
				'low': ['ffmpeg', '-i', response["path"],'-y', '-c:v', 'libx264', '-strict', 'experimental', os.path.splitext(response["path"])[0]  + ".mp4"]
			}
		}

		webm = Popen(shell['webm'][quality], stdout=PIPE)
		stdout, stderr = webm.communicate()

		mp4 = Popen(shell['mp4'][quality], stdout=PIPE)
		stdout, stderr = mp4.communicate()

		ogv = Popen(shell['ogv'][quality], stdout=PIPE)
		stdout, stderr = ogv.communicate()

		vids = {
			'mp4': os.path.splitext(response["url"])[0]  + ".mp4",
			'webm': os.path.splitext(response["url"])[0]  + ".webm",
			'ogg':  os.path.splitext(response["url"])[0]  + ".ogv"
		} 
		
		client = requests.session()
		x = client.get(env.RENDER_SUCCESS_URL)  # sets cookie
		#x = requests.get(env.RENDER_SUCCESS_URL)  # sets cookie
		csrftoken = x.text
		
		#response["response"]
		send = dict(code=data['code'], render_type=data["render_type"], urls = json.dumps(vids) , csrfmiddlewaretoken=csrftoken)
		r = client.post(env.RENDER_SUCCESS_URL, data=send, headers=dict(Referer=env.RENDER_SUCCESS_URL))
	
	except Exception as e:
		err = {'TASK-error': e}
		logger.error(err)
		return err
		


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