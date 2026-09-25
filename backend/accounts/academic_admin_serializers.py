from rest_framework import serializers

from academics.models import AcademicYear, Department, FacultySubject, Program, ProgramSubject, Section, Semester, Subject
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
    department = serializers.IntegerField(required=False)
    semester = serializers.IntegerField()
    section = serializers.IntegerField(required=False)
    academic_year = serializers.IntegerField(required=False)
    roll_number = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False)

    def validate(self, attrs):
        student = self.context["student"]
        if "section" in attrs:
            section = Section.objects.select_related("program", "semester", "academic_year").filter(pk=attrs["section"]).first()
            if not section:
                raise serializers.ValidationError({"section": "Section does not exist."})
            if section.program_id != attrs["program"]:
                raise serializers.ValidationError({"section": "Section does not belong to the selected program."})
            if section.semester_id != attrs["semester"]:
                raise serializers.ValidationError({"semester": "Section does not belong to the selected semester."})
            if attrs.get("academic_year") and section.academic_year_id != attrs["academic_year"]:
                raise serializers.ValidationError({"academic_year": "Section does not belong to the selected academic year."})
            if attrs.get("department") and section.program.department_id != attrs["department"]:
                raise serializers.ValidationError({"department": "Department does not belong to the selected program."})
        else:
            academic_year_id = attrs.get("academic_year")
            if not academic_year_id:
                latest_year = AcademicYear.objects.order_by("-start_date").first()
                if not latest_year:
                    raise serializers.ValidationError({"academic_year": "No academic year exists in the system."})
                academic_year_id = latest_year.pk
            
            section, _ = Section.objects.get_or_create(
                program_id=attrs["program"],
                semester_id=attrs["semester"],
                academic_year_id=academic_year_id,
                defaults={"section_code": "A"}
            )
            # If get_or_create didn't use defaults and returned an existing one, 
            # make sure it actually exists (it always will if get_or_create succeeds).
            
        attrs["section_object"] = section
        return attrs


class FacultyAssignmentSerializer(serializers.ModelSerializer):
    semester = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all(), required=False)
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all(), required=False)
    academic_year = serializers.PrimaryKeyRelatedField(queryset=AcademicYear.objects.all(), required=False)

    class Meta:
        model = FacultySubject
        fields = ("faculty", "subject", "academic_year", "semester", "section")
        validators = []

    def validate(self, attrs):
        subject = attrs["subject"]
        faculty = attrs["faculty"]
        
        if not isinstance(faculty, FacultyProfile):
            raise serializers.ValidationError({"faculty": "Select a faculty profile."})

        if "semester" not in attrs or "section" not in attrs:
            ps = ProgramSubject.objects.filter(subject=subject).first()
            if not ps:
                raise serializers.ValidationError({"subject": "This subject is not assigned to any program."})
            
            semester = ps.semester
            
            academic_year = attrs.get("academic_year")
            if not academic_year:
                academic_year = AcademicYear.objects.order_by("-start_date").first()
                if not academic_year:
                    raise serializers.ValidationError({"academic_year": "No academic year exists."})
                attrs["academic_year"] = academic_year
                
            section, _ = Section.objects.get_or_create(
                program=ps.program,
                semester=semester,
                academic_year=academic_year,
                defaults={"section_code": "A"}
            )
            
            attrs["semester"] = semester
            attrs["section"] = section
        else:
            section = attrs["section"]
            semester = attrs["semester"]
            if section.semester_id != semester.pk:
                raise serializers.ValidationError({"semester": "The semester must match the section."})
            if subject not in Subject.objects.filter(program_subjects__program=section.program, program_subjects__semester=semester):
                raise serializers.ValidationError({"subject": "The subject is not part of this program semester."})
                
        if FacultySubject.objects.filter(
            faculty=faculty, subject=subject, academic_year=attrs["academic_year"], semester=attrs["semester"], section=attrs["section"]
        ).exists():
            raise serializers.ValidationError("This faculty assignment already exists.")
            
        return attrs
