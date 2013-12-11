from blender_server.celery import app

import json
import socket
import requests
import os
import requests
import blender_server.config.environment as env
import sys
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

@app.task
def sendToBlender(data):
	try:
		files = getFiles(data['media_data'], data['media_url'], data['code'])
		#override url de imagenes
		data['media_url'] = files
		js = json.dumps(data)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('127.0.0.1', 13373))
		s.send(js)
		response = json.loads(s.recv(1024))
		s.close()
				
		client = requests.session()
		x = client.get(env.RENDER_SUCCESS_URL)  # sets cookie
		#x = requests.get(env.RENDER_SUCCESS_URL)  # sets cookie
		csrftoken = x.text
		
		#response["response"]
		send = dict(code=data['code'], url= response['url'] , csrfmiddlewaretoken=csrftoken)
		
		r = client.post(env.RENDER_SUCCESS_URL, data=send, headers=dict(Referer=env.RENDER_SUCCESS_URL))
		
		#return g.text
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