from rest_framework import serializers
from .models import StudentAttendance

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttendance
        fields = "__all__"
        read_only_fields = ("marked_at",)
