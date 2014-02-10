from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from .models import Render, Render_state
from .serializers import RenderSerializer

from rest_framework import viewsets
from api.serializers import UserSerializer, GroupSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import sys


from celery.task.control import revoke
from tasks import sendToBlender
import json



class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = json.dumps(data)#JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

@csrf_exempt
def render_list(request):
   
    if request.method == 'GET':
        ren = Render.objects.all()
        serializer = RenderSerializer(ren, many=True)
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = RenderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        else:
            return JSONResponse(serializer.errors, status=400)

@csrf_exempt
def render_detail(request, pk):
    
    try:
        ren = Render.objects.get(pk=pk)
    except Render.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = RenderSerializer(ren)
        return JSONResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = RenderSerializer(ren, data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data)
        else:
            return JSONResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        ren.delete()
        return HttpResponse(status=204)

#@csrf_exempt
@api_view(['POST'])
def new_render(request):
    try:
        r = sendToBlender.delay(request.DATA)
        ren = Render(code = request.DATA["code"], render_type=request.DATA["render_type"], media_url=request.DATA["media_url"], media_data = request.DATA["media_data"], task_id=r.id, render_state=Render_state.objects.get(code=1))
        ren.save()
        return JSONResponse(r.id)
    except Exception as e:
        return JSONResponse({'error_on_new': str(e)})

#@csrf_exempt
@api_view(['POST'])
def stop_render(request):
    try:
        ren = Render.objects.filter(code=request.DATA["project"], render_state= Render_state.objects.get(code=1))
        for r in ren:
            revoke(r.task_id)
            r.render_state = Render_state.objects.get(code=3)
            r.save();
        return JSONResponse("OK")
    except Exception as e:
        return JSONResponse({'error_on_stop': str(e)})