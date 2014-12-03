TCP server for Blender integration
==================


Django API
``` shell
$ cd /home/blender/blender/blender_server/
$ python2.7 manage.py runserver IP:PUERTO
```
Queue server (DO NOT USE A ROOT USER)
```shell
$ cd /home/blender/blender/blender_server/
$ su blender
$ celery -A blender_server worker -i info --concurrency=1
```
