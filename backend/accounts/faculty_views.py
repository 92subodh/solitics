from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import FacultySubject
from attendance.models import AttendanceSession, StudentAttendance
from communication.models import Post
from .faculty_serializers import FacultyPostSerializer, FacultySubjectSerializer
from .models import FacultyProfile, StudentProfile, User


class FacultyAccessMixin:
    permission_classes = [IsAuthenticated]

    def get_faculty(self, request):
        user = request.user
        if not user.is_active or not user.user_roles.filter(role__role_code=User.Role.FACULTY).exists():
            raise PermissionDenied("An active FACULTY role is required.")
        try:
            return user.employee.faculty_profile
        except (AttributeError, FacultyProfile.DoesNotExist):
            raise PermissionDenied("The authenticated user has no faculty profile.")

    def assignments(self, request):
        faculty = self.get_faculty(request)
        return FacultySubject.objects.filter(faculty=faculty).select_related(
            "subject", "semester", "academic_year"
        )

    def assignment_for(self, request, subject_id, semester_id=None, academic_year_id=None):
        assignments = self.assignments(request).filter(subject_id=subject_id)
        if semester_id:
            assignments = assignments.filter(semester_id=semester_id)
        if academic_year_id:
            assignments = assignments.filter(academic_year_id=academic_year_id)
        assignment = assignments.first()
        if not assignment:
            raise PermissionDenied("You are not assigned to this subject.")
        return assignment


class FacultySubjectsView(FacultyAccessMixin, generics.ListAPIView):
    serializer_class = FacultySubjectSerializer

    def get_queryset(self):
        return self.assignments(self.request)


class FacultyStudentsView(FacultyAccessMixin, APIView):
    def get(self, request, section_id=None):
        faculty = self.get_faculty(request)
        # Get all semesters this faculty teaches
        semester_ids = FacultySubject.objects.filter(faculty=faculty).values_list("semester_id", flat=True).distinct()
        # Get students enrolled in any of those semesters
        students = User.objects.filter(
            student_profile__enrollments__semester_id__in=semester_ids,
            student_profile__enrollments__active=True
        ).select_related("student_profile").distinct()
        return Response([
            {
                "student_id": user.student_profile.student_id,
                "name": user.display_name,
                "roll_number": user.student_profile.current_roll_number,
                "email": user.email,
                "status": user.student_profile.status,
            }
            for user in students
        ])


class FacultyAttendanceView(FacultyAccessMixin, APIView):
    def get(self, request, pk=None):
        faculty = self.get_faculty(request)
        sessions = AttendanceSession.objects.filter(faculty=faculty).select_related("subject", "semester").order_by("-attendance_date", "-start_time")
        return Response([
            {
                "attendance_session_id": session.attendance_session_id,
                "subject": session.subject.subject_name,
                "subject_id": session.subject_id,
                "semester": session.semester.semester_number if session.semester else None,
                "attendance_date": session.attendance_date,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "status": session.status,
            }
            for session in sessions
        ])

    @transaction.atomic
    def post(self, request):
        faculty = self.get_faculty(request)
        assignment = self.assignment_for(
            request,
            request.data.get("subject"),
            request.data.get("semester"),
            request.data.get("academic_year"),
        )
        session = AttendanceSession.objects.create(
            subject=assignment.subject,
            faculty=faculty,
            semester=assignment.semester,
            attendance_date=request.data.get("attendance_date"),
            start_time=request.data.get("start_time"),
            end_time=request.data.get("end_time"),
            status="SCHEDULED"
        )
        return Response({"attendance_session_id": session.attendance_session_id}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request, pk=None):
        faculty = self.get_faculty(request)
        if "records" in request.data:
            session = get_object_or_404(AttendanceSession, pk=pk, faculty=faculty)
            if session.status == "COMPLETED":
                raise ValidationError("This class is already completed.")
            records = request.data.get("records", [])
            if not isinstance(records, list) or not records:
                raise ValidationError({"records": "Provide at least one student attendance record."})
            allowed = {choice for choice, _ in StudentAttendance.Status.choices}
            for record in records:
                if record.get("status") not in allowed:
                    raise ValidationError({"records": f"Invalid attendance status: {record.get('status')}"})
                StudentAttendance.objects.create(
                    attendance_session=session,
                    student_id=record["student"],
                    status=record["status"],
                )
            session.status = "COMPLETED"
            session.save(update_fields=["status"])
            return Response({"attendance_session_id": session.attendance_session_id, "status": "COMPLETED"})

        attendance = get_object_or_404(StudentAttendance.objects.select_related("attendance_session"), pk=pk)
        if attendance.attendance_session.faculty_id != faculty.pk:
            raise PermissionDenied("You can only edit your own attendance records.")
        new_status = request.data.get("status")
        if new_status not in dict(StudentAttendance.Status.choices):
            raise ValidationError({"status": "Invalid attendance status."})
        attendance.status = new_status
        attendance.save(update_fields=("status",))
        return Response({"attendance_id": attendance.attendance_id, "status": attendance.status})


class FacultyPostView(FacultyAccessMixin, generics.ListCreateAPIView):
    serializer_class = FacultyPostSerializer

    def get_queryset(self):
        self.get_faculty(self.request)
        return Post.objects.filter(created_by=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        self.get_faculty(self.request)
        serializer.save(created_by=self.request.user, visibility="ALL")
