from datetime import date

from django.db import transaction
from django.db.models import Avg, Count, Max, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import ExamSubject, FacultySubject, Section, StudentMark, Timetable
from attendance.models import AttendanceSession, LeaveRequest, StudentAttendance
from communication.models import Notice, NoticeRecipient, Post
from .faculty_serializers import (
    FacultyLeaveRequestSerializer,
    FacultyNoticeSerializer,
    FacultyProfileSerializer,
    FacultySubjectSerializer,
    FacultyMarkSerializer,
    FacultyPostSerializer,
)
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


class FacultyDashboardView(FacultyAccessMixin, APIView):
    def get(self, request):
        faculty = self.get_faculty(request)
        assignments = self.assignments(request)
        today = timezone.localdate()
        today_classes = Timetable.objects.filter(
            faculty=faculty,
            slot__day_of_week=today.weekday(),
        ).select_related("subject", "section", "room", "slot")
        upcoming_exams = ExamSubject.objects.filter(
            subject__in=assignments.values("subject_id"),
            exam_date__gte=today,
        ).select_related("exam", "subject").order_by("exam_date")[:5]
        return Response({
            "today_classes": [
                {
                    "time": f"{entry.slot.start_time:%H:%M}",
                    "subject": entry.subject.subject_name,
                    "section": entry.section.section_code,
                    "room": entry.room.room_code,
                }
                for entry in today_classes
            ],
            "pending_attendance": AttendanceSession.objects.filter(faculty=faculty, attendance_date=today).count(),
            "upcoming_exams": [
                {"exam": item.exam.exam_name, "subject": item.subject.subject_name, "date": item.exam_date}
                for item in upcoming_exams
            ],
            "subjects_assigned": assignments.values("subject_id").distinct().count(),
            "students": Section.objects.filter(faculty_assignments__faculty=faculty).values("students").distinct().count(),
            "recent_notices": list(Notice.objects.filter(created_by=request.user).values("id", "title")[:5]),
            "pending_tasks": 0,
        })


class FacultyProfileView(FacultyAccessMixin, generics.RetrieveUpdateAPIView):
    serializer_class = FacultyProfileSerializer

    def get_object(self):
        return self.get_faculty(self.request)


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


class FacultyTimetableView(FacultyAccessMixin, APIView):
    def get(self, request):
        entries = Timetable.objects.filter(faculty=self.get_faculty(request)).select_related(
            "subject", "section", "room", "slot", "academic_year", "semester"
        )
        if request.query_params.get("today") == "true":
            entries = entries.filter(slot__day_of_week=timezone.localdate().weekday())
        return Response([
            {
                "timetable_id": entry.timetable_id,
                "day": entry.slot.day_of_week,
                "start_time": entry.slot.start_time,
                "end_time": entry.slot.end_time,
                "subject": entry.subject.subject_name,
                "section": entry.section.section_code,
                "room": entry.room.room_code,
                "academic_year": entry.academic_year.year_code,
                "semester": entry.semester.semester_number,
            }
            for entry in entries.order_by("slot__day_of_week", "slot__start_time")
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
        
        # Single record update
        attendance = get_object_or_404(StudentAttendance.objects.select_related("attendance_session"), pk=pk)
        if attendance.attendance_session.faculty_id != faculty.pk:
            raise PermissionDenied("You can only edit your own attendance records.")
        new_status = request.data.get("status")
        if new_status not in dict(StudentAttendance.Status.choices):
            raise ValidationError({"status": "Invalid attendance status."})
        attendance.status = new_status
        attendance.save(update_fields=("status",))
        return Response({"attendance_id": attendance.attendance_id, "status": attendance.status})


class FacultyAttendanceReportView(FacultyAccessMixin, APIView):
    def get(self, request):
        faculty = self.get_faculty(request)
        records = StudentAttendance.objects.filter(attendance_session__faculty=faculty)
        subject_id = request.query_params.get("subject")
        section_id = request.query_params.get("section")
        if subject_id:
            records = records.filter(attendance_session__subject_id=subject_id)
        if section_id:
            records = records.filter(attendance_session__section_id=section_id)
        summary = {status_code: records.filter(status=status_code).count() for status_code, _ in StudentAttendance.Status.choices}
        total = sum(summary.values())
        present = summary["PRESENT"] + summary["LATE"]
        return Response({"total": total, "present": present, "percentage": round((present / total) * 100, 2) if total else 0, "by_status": summary})


class FacultyExamsView(FacultyAccessMixin, APIView):
    def get(self, request):
        assignments = self.assignments(request)
        exams = ExamSubject.objects.filter(subject__in=assignments.values("subject_id")).select_related("exam", "subject")
        return Response([
            {"exam_subject_id": item.exam_subject_id, "exam": item.exam.exam_name, "subject": item.subject.subject_name, "date": item.exam_date, "max_marks": item.max_marks, "passing_marks": item.passing_marks}
            for item in exams.order_by("exam_date")
        ])


class FacultyMarksView(FacultyAccessMixin, APIView):
    def _validate_scope(self, request, exam_subject_id, student_id):
        faculty = self.get_faculty(request)
        exam_subject = get_object_or_404(ExamSubject.objects.select_related("exam", "subject"), pk=exam_subject_id)
        if not FacultySubject.objects.filter(
            faculty=faculty,
            subject=exam_subject.subject,
            semester=exam_subject.exam.semester,
            academic_year=exam_subject.exam.academic_year,
            section__student_links__student_id=student_id,
        ).exists():
            raise PermissionDenied("The student or examination subject is outside your assignment.")
        return faculty, exam_subject

    def post(self, request):
        serializer = FacultyMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        faculty, exam_subject = self._validate_scope(request, serializer.validated_data["exam_subject"], serializer.validated_data["student"])
        mark_data = dict(serializer.validated_data)
        mark_data["exam_subject"] = exam_subject
        mark_data["student_id"] = mark_data.pop("student")
        mark = StudentMark.objects.create(faculty=faculty, **mark_data)
        return Response({"marks_id": mark.marks_id, "marks_obtained": mark.marks_obtained}, status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None):
        faculty = self.get_faculty(request)
        mark = get_object_or_404(StudentMark, pk=pk, faculty=faculty)
        if "marks_obtained" in request.data:
            mark.marks_obtained = request.data["marks_obtained"]
        for field in ("internal_marks", "practical_marks", "remarks"):
            if field in request.data:
                setattr(mark, field, request.data[field])
        mark.save(update_fields=("marks_obtained", "internal_marks", "practical_marks", "remarks"))
        return Response({"marks_id": mark.marks_id, "marks_obtained": mark.marks_obtained})


class FacultyMarksReportView(FacultyAccessMixin, APIView):
    def get(self, request):
        faculty = self.get_faculty(request)
        marks = StudentMark.objects.filter(faculty=faculty)
        subject_id = request.query_params.get("subject")
        if subject_id:
            marks = marks.filter(exam_subject__subject_id=subject_id)
        summary = marks.aggregate(average=Avg("marks_obtained"), highest=Max("marks_obtained"), lowest=Min("marks_obtained"))
        return Response({"students": marks.values("student_id").distinct().count(), **summary})


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


class FacultyNoticeView(FacultyAccessMixin, generics.ListCreateAPIView):
    serializer_class = FacultyNoticeSerializer

    def get_queryset(self):
        self.get_faculty(self.request)
        return Notice.objects.filter(created_by=self.request.user).order_by("-published_at")

    @transaction.atomic
    def perform_create(self, serializer):
        section_id = self.request.data.get("section")
        assignment = self.assignments(self.request).filter(section_id=section_id).first()
        if not assignment:
            raise PermissionDenied("You can only notify an assigned section.")
        notice = serializer.save(created_by=self.request.user, audience=f"SECTION:{section_id}")
        NoticeRecipient.objects.bulk_create([
            NoticeRecipient(notice=notice, user=student.user)
            for student in assignment.section.students.select_related("user")
        ])


class FacultyLeaveView(FacultyAccessMixin, generics.ListCreateAPIView):
    serializer_class = FacultyLeaveRequestSerializer

    def get_queryset(self):
        self.get_faculty(self.request)
        return LeaveRequest.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        self.get_faculty(self.request)
        serializer.save(user=self.request.user)
