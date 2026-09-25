from django.db import models


class AttendanceSession(models.Model):
    attendance_session_id = models.BigAutoField(primary_key=True)
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT, related_name="attendance_sessions")
    faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.PROTECT, related_name="attendance_sessions")
    section = models.ForeignKey("academics.Section", on_delete=models.PROTECT, related_name="attendance_sessions")
    attendance_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, default="SCHEDULED", choices=[("SCHEDULED", "Scheduled"), ("COMPLETED", "Completed")])


class StudentAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    attendance_id = models.BigAutoField(primary_key=True)
    attendance_session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="student_attendance")
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=Status.choices)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("attendance_session", "student"), name="unique_session_student_attendance")]


class Attendance(StudentAttendance):
    class Meta:
        proxy = True


class FacultyAttendance(models.Model):
    faculty_attendance_id = models.BigAutoField(primary_key=True)
    faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.CASCADE, related_name="attendance_records")
    attendance_date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=30, default="PRESENT")


class LeaveType(models.Model):
    leave_type_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    max_days = models.PositiveSmallIntegerField(default=0)


class LeaveRequest(models.Model):
    leave_request_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="requests")
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=30, default="PENDING")
    approved_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_leave_requests")
    created_at = models.DateTimeField(auto_now_add=True)
