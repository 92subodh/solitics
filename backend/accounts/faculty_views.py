from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import FacultySubject, Section
from attendance.models import AttendanceSession, StudentAttendance
from communication.models import Post
from .faculty_serializers import FacultyPostSerializer, FacultySubjectSerializer
from .models import FacultyProfile, User


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
            "subject", "semester", "section", "academic_year"
        )

    def assignment_for(self, request, subject_id, section_id, academic_year_id=None, semester_id=None):
        assignments = self.assignments(request).filter(subject_id=subject_id, section_id=section_id)
        if academic_year_id:
            assignments = assignments.filter(academic_year_id=academic_year_id)
        if semester_id:
            assignments = assignments.filter(semester_id=semester_id)
        assignment = assignments.first()
        if not assignment:
            raise PermissionDenied("You are not assigned to this subject and section.")
        return assignment


class FacultySubjectsView(FacultyAccessMixin, generics.ListAPIView):
    serializer_class = FacultySubjectSerializer

    def get_queryset(self):
        return self.assignments(self.request)


class FacultySectionsView(FacultyAccessMixin, APIView):
    def get(self, request):
        sections = Section.objects.filter(faculty_assignments__faculty=self.get_faculty(request)).distinct()
        return Response([
            {
                "section_id": section.section_id,
                "section_code": section.section_code,
                "program": section.program.program_name,
                "semester": section.semester.semester_number,
                "academic_year": section.academic_year.year_code,
                "students": section.students.count(),
            }
            for section in sections.select_related("program", "semester", "academic_year")
        ])


class FacultyStudentsView(FacultyAccessMixin, APIView):
    def get(self, request, section_id=None):
        faculty = self.get_faculty(request)
        assignments = FacultySubject.objects.filter(faculty=faculty)
        if section_id:
            if not assignments.filter(section_id=section_id).exists():
                raise PermissionDenied("You are not assigned to this section.")
            sections = Section.objects.filter(pk=section_id)
        else:
            sections = Section.objects.filter(faculty_assignments__faculty=faculty).distinct()
        students = User.objects.filter(student_profile__sections__in=sections).select_related("person", "student_profile").distinct()
        return Response([
            {
                "student_id": user.student_profile.student_id,
                "name": user.display_name,
                "roll_number": user.student_profile.current_roll_number,
                "email": user.email,
                "section_ids": list(user.student_profile.sections.filter(section_id__in=sections.values("section_id")).values_list("section_id", flat=True)),
                "status": user.student_profile.status,
            }
            for user in students
        ])


class FacultyAttendanceView(FacultyAccessMixin, APIView):
    def get(self, request, pk=None):
        faculty = self.get_faculty(request)
        sessions = AttendanceSession.objects.filter(faculty=faculty).select_related("subject", "section").order_by("-attendance_date", "-start_time")
        return Response([
            {
                "attendance_session_id": session.attendance_session_id,
                "subject": session.subject.subject_name,
                "subject_id": session.subject_id,
                "section": session.section.section_code,
                "section_id": session.section_id,
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
            request.data.get("section"),
            request.data.get("academic_year"),
            request.data.get("semester"),
        )
        session = AttendanceSession.objects.create(
            subject=assignment.subject,
            faculty=faculty,
            section=assignment.section,
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
            section_student_ids = set(session.section.students.values_list("student_id", flat=True))
            invalid = [record.get("student") for record in records if record.get("student") not in section_student_ids]
            if invalid:
                raise ValidationError({"records": "Every student must belong to the assigned section."})
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
        section_id = self.request.data.get("section")
        if not self.assignments(self.request).filter(section_id=section_id).exists():
            raise PermissionDenied("You can only post to an assigned section.")
        serializer.save(created_by=self.request.user, visibility=f"SECTION:{section_id}")
