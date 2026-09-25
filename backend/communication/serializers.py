from rest_framework import serializers
from .models import Notice, Post

class NoticeSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Notice 
        fields = "__all__" 
        read_only_fields = ("created_by", "published_at")

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ("created_by", "created_at")
