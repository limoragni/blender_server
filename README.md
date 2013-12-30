blender_server
==============

Para correr el servidor de renderizado:

Primero se levanta el django que contiene la API para comunicarse con el frontend

Primero hay que ubicarse en el directorio que contiene el server

$ cd /home/blender/blender/blender_server/

Ejecutar el server

$ python2.7 manage.py runserver IP:PUERTO

Luego se levanta el servidor de encolado Celery

$ cd /home/blender/blender/blender_server/

$ su blender
$ celery -A blender_server worker -i info --concurrency=1
