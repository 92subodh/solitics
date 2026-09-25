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
        LIBRARIAN = "LIBRARIAN", "Librarian"
        STUDENT = "STUDENT", "Student"
        PARENT = "PARENT", "Parent"

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


class Permission(models.Model):
    permission_code = models.CharField(max_length=80, unique=True)
    permission_name = models.CharField(max_length=150)
    module = models.CharField(max_length=80)


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="roles")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("role", "permission"), name="unique_role_permission")]


class UserSession(models.Model):
    session_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    refresh_token_hash = models.CharField(max_length=255)
    device_info = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class PasswordResetToken(models.Model):
    token_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)


class AuditLog(models.Model):
    audit_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


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


class StudentGuardian(models.Model):
    guardian_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="guardians")
    guardian_name = models.CharField(max_length=120)
    relation = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)


class ParentProfile(models.Model):
    parent_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    parent_code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    children = models.ManyToManyField(StudentProfile, through="ParentStudent", related_name="parents")

    def __str__(self):
        return self.user.display_name


class ParentStudent(models.Model):
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name="student_links")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="parent_links")
    relation = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    can_view_attendance = models.BooleanField(default=True)
    can_view_results = models.BooleanField(default=True)
    can_pay_fees = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("parent", "student"), name="unique_parent_student")]


class FacultyProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="faculty_profile")
    department = models.ForeignKey("academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="faculty_members")
    specialization = models.CharField(max_length=200, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    designation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.employee.user.display_name


class LibrarianProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="librarian_profile")
    shift = models.CharField(max_length=50, blank=True)
    library_section = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.employee.user.display_name


class AdminProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="admin_profile")
    admin_level = models.CharField(max_length=50, blank=True)
    office_name = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.employee.user.display_name


class Address(models.Model):
    address_id = models.BigAutoField(primary_key=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20)


class PersonAddress(models.Model):
    person_address_id = models.BigAutoField(primary_key=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="addresses")
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="people")
    address_type = models.CharField(max_length=30)
    is_primary = models.BooleanField(default=False)


class StudentDocument(models.Model):
    document_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=80)
    file_url = models.URLField()
    status = models.CharField(max_length=30, default="PENDING")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)


class FacultySalary(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name="salary_records")
    month = models.DateField(help_text="Use the first day of the salary month.")
    basic_amount = models.DecimalField(max_digits=12, decimal_places=2)
    allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        unique_together = ("faculty", "month")
        ordering = ("-month",)

    @property
    def net_amount(self): return self.basic_amount + self.allowance - self.deduction
