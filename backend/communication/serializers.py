from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = Post
        fields = ("post_id", "title", "content", "image_url", "visibility", "created_at", "created_by", "created_by_name")
        read_only_fields = ("post_id", "created_by", "created_at")
