from rest_framework import viewsets
from accounts.permissions import IsAdminOrReadOnly
from .models import Notice, Post
from .serializers import NoticeSerializer, PostSerializer

class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.select_related("created_by").all()
    serializer_class = NoticeSerializer
    permission_classes = [IsAdminOrReadOnly]
    def perform_create(self, serializer): 
        serializer.save(created_by=self.request.user)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("created_by").all()
    serializer_class = PostSerializer
    permission_classes = [IsAdminOrReadOnly]
    def perform_create(self, serializer): 
        serializer.save(created_by=self.request.user)
