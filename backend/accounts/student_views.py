from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from attendance.models import StudentAttendance
from communication.models import Post


class StudentAccessMixin:
    permission_classes = [IsAuthenticated]

    def get_student_profile(self, request):
        user = request.user
        if not user.is_active or not user.user_roles.filter(role__role_code=User.Role.STUDENT).exists():
            raise PermissionDenied("An active STUDENT role is required.")
        if not hasattr(user, "student_profile"):
            raise PermissionDenied("The authenticated user has no student profile.")
        return user.student_profile


class StudentProfileView(StudentAccessMixin, APIView):
    def get(self, request):
        profile = self.get_student_profile(request)
        user = request.user
        
        return Response({
            "name": user.display_name,
            "email": user.email,
            "phone": user.phone,
            "roll_number": profile.roll_number,
            "admission_number": profile.admission_number,
            "program": profile.program.program_name if profile.program else None,
            "department": profile.department.department_name if profile.department else None,
            "semester": profile.current_semester,
            "status": profile.status,
            "guardian_name": profile.guardian_name,
            "guardian_phone": profile.guardian_phone,
        })


class StudentAttendanceView(StudentAccessMixin, APIView):
    def get(self, request):
        profile = self.get_student_profile(request)
        
        records = StudentAttendance.objects.filter(student=profile).select_related(
            "attendance_session", "attendance_session__subject"
        ).order_by("-attendance_session__attendance_date")
        
        total_sessions = records.count()
        attended_sessions = records.filter(status__in=["PRESENT", "LATE"]).count()
        
        history = [
            {
                "date": record.attendance_session.attendance_date,
                "subject": record.attendance_session.subject.subject_name,
                "status": record.status,
            }
            for record in records
        ]
        
        return Response({
            "total": total_sessions,
            "attended": attended_sessions,
            "overall_percentage": round((attended_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1),
            "history": history
        })

class StudentPostView(StudentAccessMixin, APIView):
    def get(self, request):
        self.get_student_profile(request)
        posts = Post.objects.filter(visibility="ALL").select_related("created_by").order_by("-created_at")
        return Response([
            {
                "post_id": post.post_id,
                "title": post.title,
                "content": post.content,
                "author": post.created_by.display_name,
                "visibility": post.visibility,
                "created_at": post.created_at,
            }
            for post in posts
        ])
