from rest_framework import viewsets
from accounts.permissions import IsAdminOrReadOnly
from .models import StudentAttendance
from .serializers import AttendanceSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = StudentAttendance.objects.select_related("student", "attendance_session", "attendance_session__subject").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrReadOnly]
