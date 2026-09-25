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
    max_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)
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


class AcademicCalendar(models.Model):
    calendar_id = models.BigAutoField(primary_key=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="calendar_events")
    event_name = models.CharField(max_length=150)
    event_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)


class Room(models.Model):
    room_id = models.BigAutoField(primary_key=True)
    room_code = models.CharField(max_length=30, unique=True)
    building = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=30, blank=True)
    room_type = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(default=0)


class TimeSlot(models.Model):
    slot_id = models.BigAutoField(primary_key=True)
    day_of_week = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()


class Timetable(models.Model):
    timetable_id = models.BigAutoField(primary_key=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="timetable_entries")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="timetable_entries")
    faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.PROTECT, related_name="timetable_entries")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="timetable_entries")
    slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name="timetable_entries")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="timetable_entries")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="timetable_entries")


class ExamType(models.Model):
    exam_type_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)


class Exam(models.Model):
    exam_id = models.BigAutoField(primary_key=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.PROTECT, related_name="exams")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="exams")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="exams")
    exam_name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()


class ExamSubject(models.Model):
    exam_subject_id = models.BigAutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="exam_subjects")
    exam_date = models.DateField()
    max_marks = models.PositiveIntegerField()
    passing_marks = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=("exam", "subject"), name="unique_exam_subject")]


class StudentMark(models.Model):
    marks_id = models.BigAutoField(primary_key=True)
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name="student_marks")
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="marks")
    faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.PROTECT, related_name="entered_marks")
    marks_obtained = models.DecimalField(max_digits=7, decimal_places=2)
    internal_marks = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    practical_marks = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    entered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("exam_subject", "student"), name="unique_exam_subject_student")]


class GradingScale(models.Model):
    grade_id = models.BigAutoField(primary_key=True)
    grade = models.CharField(max_length=10)
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2)


class StudentResult(models.Model):
    result_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="results")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    total_marks = models.DecimalField(max_digits=10, decimal_places=2)
    obtained_marks = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    result_status = models.CharField(max_length=30)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("student", "exam"), name="unique_student_exam_result")]


class GradeCard(models.Model):
    grade_card_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="grade_cards")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="grade_cards")
    certificate_number = models.CharField(max_length=80, unique=True)
    issue_date = models.DateField()
    pdf_url = models.URLField(blank=True)
