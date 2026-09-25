from django.db import models


class Department(models.Model):
    department_code = models.CharField(max_length=12, unique=True)
    department_name = models.CharField(max_length=120, unique=True)
    head_faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="headed_departments")
    class Meta: ordering = ("department_name",)
    def __str__(self): return self.department_name


class Program(models.Model):
    program_code = models.CharField(max_length=20, unique=True)
    program_name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="programs")
    degree_type = models.CharField(max_length=50, blank=True)
    duration_years = models.PositiveSmallIntegerField(default=3)
    class Meta: ordering = ("program_name",)
    def __str__(self): return self.program_name


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="courses")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    duration_years = models.PositiveSmallIntegerField(default=3)
    class Meta: ordering = ("name",)
    def __str__(self): return self.name


class AcademicYear(models.Model):
    year_code = models.CharField(max_length=9, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    def __str__(self): return self.year_code


class Semester(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="semesters")
    semester_number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=80, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("program", "semester_number"), name="unique_program_semester")]


class Subject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="subjects", null=True, blank=True)
    subject_code = models.CharField(max_length=20, unique=True)
    subject_name = models.CharField(max_length=150)
    subject_type = models.CharField(max_length=50, blank=True)
    credits = models.PositiveSmallIntegerField(default=3)
    class Meta: ordering = ("subject_code",)
    def __str__(self): return self.subject_code


class ProgramSubject(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="program_subjects")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="program_subjects")
    is_core = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("program", "semester", "subject"), name="unique_program_subject")]


class FacultySubject(models.Model):
    faculty_subject_id = models.BigAutoField(primary_key=True)
    faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.CASCADE, related_name="subject_assignments")
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT, related_name="faculty_assignments")
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT, related_name="faculty_assignments")
    semester = models.ForeignKey("academics.Semester", on_delete=models.PROTECT, related_name="faculty_assignments")
    section = models.ForeignKey("academics.Section", on_delete=models.PROTECT, related_name="faculty_assignments")

    class Meta:
        ordering = ("academic_year", "semester", "section", "subject")
        constraints = [
            models.UniqueConstraint(
                fields=("faculty", "subject", "academic_year", "semester", "section"),
                name="unique_faculty_subject_assignment",
            )
        ]


class Enrollment(models.Model):
    enrollment_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="enrollments")
    program = models.ForeignKey(Program, on_delete=models.PROTECT, null=True, blank=True, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, null=True, blank=True, related_name="enrollments")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, null=True, blank=True, related_name="enrollments")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, null=True, blank=True, related_name="enrollments")
    roll_number = models.CharField(max_length=30, blank=True)
    section = models.CharField(max_length=30, blank=True)
    enrollment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, default="ACTIVE")
    active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("student", "academic_year", "semester"), name="unique_student_academic_enrollment")]


class Section(models.Model):
    section_id = models.BigAutoField(primary_key=True)
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="sections")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="sections")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="sections")
    section_code = models.CharField(max_length=30)
    capacity = models.PositiveIntegerField(default=60)
    students = models.ManyToManyField("accounts.StudentProfile", through="SectionStudent", related_name="sections")
    class Meta:
        constraints = [models.UniqueConstraint(fields=("program", "semester", "academic_year", "section_code"), name="unique_academic_section")]


class SectionStudent(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="student_links")
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="section_links")
    assigned_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("section", "student"), name="unique_section_student")]
