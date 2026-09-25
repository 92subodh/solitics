from rest_framework import serializers
from .models import Attendance
class AttendanceSerializer(serializers.ModelSerializer):
    class Meta: model = Attendance; fields = "__all__"; read_only_fields = ("marked_at",)
