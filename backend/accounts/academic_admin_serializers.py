from rest_framework import serializers

from academics.models import AcademicYear, Department, FacultySubject, Program, ProgramSubject, Semester, Subject
from .models import FacultyProfile, StudentProfile


class AdminDepartmentCreateSerializer(serializers.ModelSerializer):
    program_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = ("id", "department_code", "department_name", "program_count")
        read_only_fields = ("id",)

    def validate_department_code(self, value):
        if Department.objects.filter(department_code__iexact=value).exists():
            raise serializers.ValidationError("A department with this code already exists.")
        return value.upper()

    def validate_department_name(self, value):
        if Department.objects.filter(department_name__iexact=value).exists():
            raise serializers.ValidationError("A department with this name already exists.")
        return value


class ProgramCourseSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=150)
    credits = serializers.IntegerField(min_value=0, default=3)
    subject_type = serializers.CharField(max_length=50, required=False, allow_blank=True, default="CORE")
    is_core = serializers.BooleanField(default=True)


class ProgramSemesterSerializer(serializers.Serializer):
    semester_number = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    courses = ProgramCourseSerializer(many=True, required=False, default=list)


class AdminProgramCreateSerializer(serializers.Serializer):
    program_code = serializers.CharField(max_length=20)
    program_name = serializers.CharField(max_length=150)
    department = serializers.IntegerField()
    degree_type = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    duration_years = serializers.IntegerField(min_value=1, default=4)
    semesters = ProgramSemesterSerializer(many=True)

    def validate(self, attrs):
        from academics.models import Department
        if not Department.objects.filter(pk=attrs["department"]).exists():
            raise serializers.ValidationError({"department": "Department does not exist."})
        if Program.objects.filter(program_code=attrs["program_code"]).exists():
            raise serializers.ValidationError({"program_code": "A program with this code already exists."})
        semester_numbers = [item["semester_number"] for item in attrs["semesters"]]
        if len(semester_numbers) != len(set(semester_numbers)):
            raise serializers.ValidationError({"semesters": "Semester numbers must be unique."})
        if sorted(semester_numbers) != list(range(1, len(semester_numbers) + 1)):
            raise serializers.ValidationError({"semesters": "Semesters must start at 1 and be consecutive."})
        course_codes = []
        for semester in attrs["semesters"]:
            for course in semester["courses"]:
                course_codes.append(course["code"])
        if len(course_codes) != len(set(course_codes)):
            raise serializers.ValidationError({"semesters": "Course codes must be unique across the program."})
        return attrs


class StudentAcademicPlacementSerializer(serializers.Serializer):
    program = serializers.IntegerField()
    semester = serializers.IntegerField()
    academic_year = serializers.IntegerField(required=False)
    roll_number = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False)

    def validate(self, attrs):
        if not Program.objects.filter(pk=attrs["program"]).exists():
            raise serializers.ValidationError({"program": "Program does not exist."})
        if not Semester.objects.filter(pk=attrs["semester"], program_id=attrs["program"]).exists():
            raise serializers.ValidationError({"semester": "Semester does not belong to the selected program."})
        if "academic_year" in attrs and not AcademicYear.objects.filter(pk=attrs["academic_year"]).exists():
            raise serializers.ValidationError({"academic_year": "Academic year does not exist."})
        return attrs


class FacultyAssignmentSerializer(serializers.ModelSerializer):
    semester = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all(), required=False)
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all(), required=False)

    faculty_name = serializers.SerializerMethodField(read_only=True)
    subject_code = serializers.CharField(source="subject.subject_code", read_only=True)
    subject_name = serializers.CharField(source="subject.subject_name", read_only=True)
    semester_number = serializers.IntegerField(source="semester.semester_number", read_only=True)
    academic_year_code = serializers.CharField(source="academic_year.year_code", read_only=True)

    class Meta:
        model = FacultySubject
        fields = (
            "faculty_subject_id", "faculty", "faculty_name",
            "subject", "subject_code", "subject_name",
            "semester", "semester_number",
            "academic_year", "academic_year_code",
        )
        validators = []

    def get_faculty_name(self, obj):
        try:
            return obj.faculty.employee.user.display_name
        except Exception:
            return None

    def validate(self, attrs):
        subject = attrs["subject"]
        faculty = attrs["faculty"]

        if not isinstance(faculty, FacultyProfile):
            raise serializers.ValidationError({"faculty": "Select a faculty profile."})

        if "semester" not in attrs:
            ps = ProgramSubject.objects.filter(subject=subject).first()
            if not ps:
                raise serializers.ValidationError({"subject": "This subject is not assigned to any program."})
            attrs["semester"] = ps.semester

        if "academic_year" not in attrs:
            academic_year = AcademicYear.objects.order_by("-start_date").first()
            if not academic_year:
                raise serializers.ValidationError({"academic_year": "No academic year exists."})
            attrs["academic_year"] = academic_year

        if FacultySubject.objects.filter(
            faculty=faculty, subject=subject, academic_year=attrs["academic_year"], semester=attrs["semester"]
        ).exists():
            raise serializers.ValidationError("This faculty assignment already exists.")

        return attrs
