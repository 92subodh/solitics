from rest_framework import viewsets
from accounts.permissions import IsAdminOrReadOnly
from .models import Department, Course, Subject, Enrollment
from .serializers import DepartmentSerializer, CourseSerializer, SubjectSerializer, EnrollmentSerializer
class BaseViewSet(viewsets.ModelViewSet): permission_classes = [IsAdminOrReadOnly]
class DepartmentViewSet(BaseViewSet): queryset = Department.objects.all(); serializer_class = DepartmentSerializer
class CourseViewSet(BaseViewSet): queryset = Course.objects.select_related("department").all(); serializer_class = CourseSerializer
class SubjectViewSet(BaseViewSet): queryset = Subject.objects.select_related("course").all(); serializer_class = SubjectSerializer
class EnrollmentViewSet(BaseViewSet): queryset = Enrollment.objects.select_related("student", "program", "course", "academic_year", "semester").all(); serializer_class = EnrollmentSerializer
