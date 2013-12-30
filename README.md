Servido de Blender
==================

Para correr el servidor de renderizado:

Primero se levanta el django que contiene la API para comunicarse con el frontend

``` shell
$ cd /home/blender/blender/blender_server/
$ python2.7 manage.py runserver IP:PUERTO
```
Luego se levanta el servidor de encolado Celery. Utilizando un usuario que no sea root por razones de seguridad.
```shell
$ cd /home/blender/blender/blender_server/
$ su blender
$ celery -A blender_server worker -i info --concurrency=1
```
