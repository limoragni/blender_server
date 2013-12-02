from django.contrib.auth.models import User, Group
from .models import Render
from rest_framework import serializers

class RenderSerializer(serializers.Serializer):
	pk = serializers.Field() 
	code = serializers.CharField(max_length=200)
	media_url = serializers.CharField(max_length=200)
	media_data = serializers.CharField(max_length=2000)

	def restore_object(self, attrs, instance=None):
		if instance:
			instance.code = attrs.get('code', instance.code)
			instance.media_url = attrs.get('media_url', instance.media_url)
			instance.media_data = attrs.get('media_data', instance.media_data)
			return instance

		# Create new instance
		return Render(**attrs)

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')