from django.conf import settings
from django.db import models
from academics.models import Course
class FeeStructure(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="fee_structures")
    academic_year = models.CharField(max_length=9)
    semester = models.PositiveSmallIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    program = models.ForeignKey("academics.Program", on_delete=models.PROTECT, null=True, blank=True, related_name="fee_structures")
    academic_year_record = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT, null=True, blank=True, related_name="fee_structures")
    fee_category = models.ForeignKey("fees.FeeCategory", on_delete=models.PROTECT, null=True, blank=True, related_name="fee_structures")
    class Meta: unique_together = ("course", "academic_year", "semester")
class Payment(models.Model):
    class Status(models.TextChoices): PENDING = "PENDING", "Pending"; PAID = "PAID", "Paid"; FAILED = "FAILED", "Failed"
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True, unique=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    invoice = models.ForeignKey("fees.FeeInvoice", on_delete=models.PROTECT, null=True, blank=True, related_name="payments")
    student_profile = models.ForeignKey("accounts.StudentProfile", on_delete=models.PROTECT, null=True, blank=True, related_name="payments")
    class Meta: ordering = ("-id",)


class FeeCategory(models.Model):
    fee_category_id = models.BigAutoField(primary_key=True)
    category_code = models.CharField(max_length=30, unique=True)
    category_name = models.CharField(max_length=100)


class StudentFeeAccount(models.Model):
    fee_account_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="fee_accounts")
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT, related_name="student_fee_accounts")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, default="PENDING")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("student", "academic_year"), name="unique_student_fee_account")]


class FeeInvoice(models.Model):
    invoice_id = models.BigAutoField(primary_key=True)
    fee_account = models.ForeignKey(StudentFeeAccount, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, default="PENDING")


class FeeInvoiceItem(models.Model):
    invoice_item_id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name="items")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="invoice_items")
    amount = models.DecimalField(max_digits=12, decimal_places=2)


class Receipt(models.Model):
    receipt_id = models.BigAutoField(primary_key=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=50, unique=True)
    receipt_url = models.URLField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)


class Scholarship(models.Model):
    scholarship_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class StudentScholarship(models.Model):
    student_scholarship_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="scholarships")
    scholarship = models.ForeignKey(Scholarship, on_delete=models.PROTECT, related_name="awards")
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.PROTECT, related_name="scholarships")
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, default="PENDING")
