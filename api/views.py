from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from .models import Render
from .serializers import RenderSerializer

from rest_framework import viewsets
from api.serializers import UserSerializer, GroupSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import sys

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
    """
    List all code snippets, or create a new snippet.
    """
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
    """
    Retrieve, update or delete a code snippet.
    """
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
        ren = Render(code = request.DATA["code"], render_type=request.DATA["render_type"], media_url=request.DATA["media_url"], media_data = request.DATA["media_data"])
        ren.save()
        r = sendToBlender.delay(request.DATA)
        return JSONResponse(r)
    except Exception as e:
        return JSONResponse({'error': str(e)})