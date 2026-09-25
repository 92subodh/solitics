from django.contrib.auth.models import AbstractUser
from django.db import models


class Person(models.Model):
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    nationality = models.CharField(max_length=80, blank=True)
    profile_photo = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return " ".join(part for part in (self.first_name, self.last_name) if part).strip()


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"

    person = models.OneToOneField(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="user")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_name(self):
        return self.get_full_name() or self.username


class Role(models.Model):
    role_code = models.CharField(max_length=20, unique=True)
    role_name = models.CharField(max_length=100)


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "role"), name="unique_user_role")]


class Employee(models.Model):
    employee_code = models.IntegerField(unique=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee")
    department = models.ForeignKey("academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    joining_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, default="ACTIVE")


class StudentProfile(models.Model):
    student_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    admission_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    program = models.ForeignKey("academics.Program", on_delete=models.PROTECT, null=True, blank=True, related_name="students")
    department = models.ForeignKey("academics.Department", on_delete=models.PROTECT, null=True, blank=True, related_name="students")
    admission_date = models.DateField(null=True, blank=True)
    current_semester = models.PositiveSmallIntegerField(null=True, blank=True)
    current_roll_number = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=30, default="ACTIVE")
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)

    @property
    def roll_number(self):
        return self.current_roll_number

    def __str__(self):
        return f"{self.current_roll_number or self.user.username} - {self.user.display_name}"


class FacultyProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="faculty_profile")
    department = models.ForeignKey("academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="faculty_members")
    specialization = models.CharField(max_length=200, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    designation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.employee.user.display_name


class AdminProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="admin_profile")
    admin_level = models.CharField(max_length=50, blank=True)
    office_name = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.employee.user.display_name
