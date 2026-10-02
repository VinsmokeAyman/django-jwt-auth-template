from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

	password = serializers.CharField(write_only=True, required=True, min_length=8)

	class Meta:
		model = User
		fields = "__all__"
		read_only_fields = ("id",)