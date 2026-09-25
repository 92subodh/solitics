from django.db import transaction
from django.db.models import Q
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import AcademicYear, Department, FacultySubject, Program, ProgramSubject, Section, SectionStudent, Semester, Subject
from .academic_admin_serializers import AdminDepartmentCreateSerializer, AdminProgramCreateSerializer, FacultyAssignmentSerializer, StudentAcademicPlacementSerializer
from .models import FacultyProfile, StudentProfile, User


class AdminAcademicMixin:
    permission_classes = [IsAuthenticated]

    def ensure_admin(self, request):
        if not request.user.is_active or not request.user.user_roles.filter(role__role_code=User.Role.ADMIN).exists():
            raise PermissionDenied("An active ADMIN role is required.")


class AdminAcademicOptionsView(AdminAcademicMixin, APIView):
    def get(self, request):
        self.ensure_admin(request)
        return Response({
            "departments": list(Department.objects.order_by("department_name").values("id", "department_code", "department_name")),
            "students": list(StudentProfile.objects.select_related("user").order_by("user__last_name", "user__first_name").values("student_id", "user__first_name", "user__last_name", "admission_number", "current_roll_number")),
            "faculty": list(FacultyProfile.objects.select_related("employee__user").order_by("employee__user__last_name").values("id", "employee__user__first_name", "employee__user__last_name", "employee__employee_code")),
            "programs": list(Program.objects.order_by("program_name").values("id", "program_code", "program_name", "department_id")),
            "semesters": list(Semester.objects.order_by("program_id", "semester_number").values("id", "program_id", "semester_number", "name")),
            "academic_years": list(AcademicYear.objects.order_by("-start_date").values("id", "year_code")),
            "sections": list(Section.objects.order_by("program_id", "section_code").values("section_id", "program_id", "semester_id", "academic_year_id", "section_code")),
            "subjects": list(Subject.objects.order_by("subject_code").values("id", "subject_code", "subject_name")),
        })


class AdminDepartmentView(AdminAcademicMixin, generics.ListCreateAPIView):
    serializer_class = AdminDepartmentCreateSerializer

    def get_queryset(self):
        self.ensure_admin(self.request)
        from django.db.models import Count
        return Department.objects.annotate(program_count=Count('programs')).order_by("department_name")

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()


class AdminProgramCreateView(AdminAcademicMixin, APIView):
    def get(self, request):
        self.ensure_admin(request)
        programs = Program.objects.select_related("department").prefetch_related(
            "semesters", "program_subjects__subject"
        ).order_by("program_name")

        data = []
        for p in programs:
            semesters = []
            course_count = 0
            for sem in p.semesters.all():
                courses = []
                for ps in p.program_subjects.all():
                    if ps.semester_id == sem.id:
                        courses.append({
                            "subject_id": ps.subject.pk,
                            "code": ps.subject.subject_code,
                            "name": ps.subject.subject_name,
                            "credits": ps.subject.credits,
                            "is_core": ps.is_core
                        })
                        course_count += 1
                semesters.append({
                    "semester_id": sem.pk,
                    "semester_number": sem.semester_number,
                    "courses": courses
                })

            data.append({
                "id": p.id,
                "program_code": p.program_code,
                "program_name": p.program_name,
                "department_id": p.department_id,
                "department_name": p.department.department_name,
                "degree_type": p.degree_type,
                "duration_years": p.duration_years,
                "semester_count": len(semesters),
                "course_count": course_count,
                "semesters": semesters
            })
        return Response(data)

    @transaction.atomic
    def post(self, request):
        self.ensure_admin(request)
        serializer = AdminProgramCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        program = Program.objects.create(
            program_code=data["program_code"],
            program_name=data["program_name"],
            department_id=data["department"],
            degree_type=data["degree_type"],
            duration_years=data["duration_years"],
        )
        created_semesters = []
        created_subjects = 0
        for semester_data in data["semesters"]:
            semester = Semester.objects.create(
                program=program,
                semester_number=semester_data["semester_number"],
                name=semester_data.get("name") or f"Semester {semester_data['semester_number']}",
            )
            semester_courses = []
            for course in semester_data["courses"]:
                subject, created = Subject.objects.get_or_create(
                    subject_code=course["code"],
                    defaults={
                        "subject_name": course["name"],
                        "subject_type": course["subject_type"],
                        "credits": course["credits"],
                    },
                )
                if not created and subject.subject_name != course["name"]:
                    raise serializers.ValidationError({"semesters": f"Course code {course['code']} already belongs to another subject."})
                ProgramSubject.objects.create(
                    program=program,
                    semester=semester,
                    subject=subject,
                    is_core=course["is_core"],
                )
                semester_courses.append({"subject_id": subject.pk, "code": subject.subject_code, "name": subject.subject_name})
                created_subjects += 1
            created_semesters.append({"semester_id": semester.pk, "semester_number": semester.semester_number, "courses": semester_courses})
        return Response({"program_id": program.pk, "program_code": program.program_code, "program_name": program.program_name, "semesters": created_semesters, "course_count": created_subjects}, status=status.HTTP_201_CREATED)


class AdminProgramDetailView(AdminAcademicMixin, APIView):
    @transaction.atomic
    def patch(self, request, pk):
        self.ensure_admin(request)
        try:
            program = Program.objects.get(pk=pk)
        except Program.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        data = request.data

        if "remove_subject_ids" in data and data["remove_subject_ids"]:
            ProgramSubject.objects.filter(
                program=program,
                subject_id__in=data["remove_subject_ids"]
            ).delete()

        if "semesters" in data:
            for semester_data in data["semesters"]:
                semester, _ = Semester.objects.get_or_create(
                    program=program,
                    semester_number=semester_data["semester_number"],
                    defaults={"name": semester_data.get("name") or f"Semester {semester_data['semester_number']}"}
                )
                for course in semester_data.get("courses", []):
                    subject, created = Subject.objects.get_or_create(
                        subject_code=course["code"],
                        defaults={
                            "subject_name": course["name"],
                            "subject_type": course.get("subject_type", "CORE"),
                            "credits": course.get("credits", 3),
                        },
                    )
                    ProgramSubject.objects.get_or_create(
                        program=program,
                        semester=semester,
                        subject=subject,
                        defaults={"is_core": course.get("is_core", True)}
                    )

        return Response({"detail": "Program updated successfully."})


class AdminStudentAcademicView(AdminAcademicMixin, APIView):
    def get(self, request, pk):
        self.ensure_admin(request)
        student = StudentProfile.objects.select_related("user", "program", "department").get(pk=pk)
        section = student.sections.select_related("program", "semester", "academic_year").order_by("-section_id").first()
        return Response({
            "student_id": student.student_id,
            "name": student.user.display_name,
            "admission_number": student.admission_number,
            "program": student.program_id,
            "department": student.department_id,
            "semester": student.current_semester,
            "section": section.section_id if section else None,
            "academic_year": section.academic_year_id if section else None,
            "roll_number": student.current_roll_number,
            "status": student.status,
        })

    @transaction.atomic
    def patch(self, request, pk):
        self.ensure_admin(request)
        student = StudentProfile.objects.select_related("user").get(pk=pk)
        serializer = StudentAcademicPlacementSerializer(data=request.data, context={"student": student})
        serializer.is_valid(raise_exception=True)
        placement = serializer.validated_data
        section = placement["section_object"]
        student.program_id = section.program_id
        student.department_id = section.program.department_id
        student.current_semester = section.semester.semester_number
        if "roll_number" in placement:
            student.current_roll_number = placement["roll_number"]
        if "status" in placement:
            student.status = placement["status"]
        student.save(update_fields=("program", "department", "current_semester", "current_roll_number", "status"))
        SectionStudent.objects.filter(student=student).exclude(section=section).delete()
        SectionStudent.objects.get_or_create(section=section, student=student)
        enrollment, _ = student.enrollments.update_or_create(
            academic_year=section.academic_year,
            semester=section.semester,
            defaults={
                "program": section.program,
                "roll_number": student.current_roll_number,
                "section": section.section_code,
                "status": student.status,
                "active": True,
            },
        )
        return Response({
            "student_id": student.student_id,
            "program": section.program_id,
            "department": section.program.department_id,
            "semester": section.semester.semester_number,
            "section": section.section_id,
            "academic_year": section.academic_year_id,
            "roll_number": student.current_roll_number,
            "enrollment_id": enrollment.enrollment_id,
        })


class AdminFacultyAssignmentView(AdminAcademicMixin, generics.ListCreateAPIView):
    serializer_class = FacultyAssignmentSerializer

    def get_queryset(self):
        self.ensure_admin(self.request)
        queryset = FacultySubject.objects.select_related(
            "faculty__employee__user", "subject", "section__program", "semester", "academic_year"
        ).order_by("faculty__employee__user__last_name", "subject__subject_code")
        faculty = self.request.query_params.get("faculty")
        program = self.request.query_params.get("program")
        section = self.request.query_params.get("section")
        if faculty:
            queryset = queryset.filter(faculty_id=faculty)
        if program:
            queryset = queryset.filter(section__program_id=program)
        if section:
            queryset = queryset.filter(section_id=section)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()


class AdminFacultyAssignmentDetailView(AdminAcademicMixin, APIView):
    def delete(self, request, pk):
        self.ensure_admin(request)
        assignment = FacultySubject.objects.get(pk=pk)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
