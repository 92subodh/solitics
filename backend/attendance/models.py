from django.db import models


class AttendanceSession(models.Model):
    attendance_session_id = models.BigAutoField(primary_key=True)
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT, related_name="attendance_sessions")
    faculty = models.ForeignKey("accounts.FacultyProfile", on_delete=models.PROTECT, related_name="attendance_sessions")
    semester = models.ForeignKey("academics.Semester", on_delete=models.PROTECT, related_name="attendance_sessions", null=True, blank=True)
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
