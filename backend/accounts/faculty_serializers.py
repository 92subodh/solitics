from rest_framework import serializers

from academics.models import FacultySubject
from attendance.models import StudentAttendance
from communication.models import Post
from .models import FacultyProfile


class FacultySubjectSerializer(serializers.ModelSerializer):
    subject_code = serializers.CharField(source="subject.subject_code", read_only=True)
    subject_name = serializers.CharField(source="subject.subject_name", read_only=True)
    semester_number = serializers.IntegerField(source="semester.semester_number", read_only=True)
    section_code = serializers.CharField(source="section.section_code", read_only=True)
    academic_year_code = serializers.CharField(source="academic_year.year_code", read_only=True)

    class Meta:
        model = FacultySubject
        fields = (
            "faculty_subject_id", "subject", "subject_code", "subject_name", "semester",
            "semester_number", "section", "section_code", "academic_year", "academic_year_code",
        )
        read_only_fields = fields


class StudentAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttendance
        fields = "__all__"
        read_only_fields = ("marked_at",)


class FacultyPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("post_id", "title", "content", "image_url", "visibility", "created_at")
        read_only_fields = ("post_id", "created_at")
