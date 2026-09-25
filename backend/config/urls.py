from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import AdminRoleListView, AdminUserViewSet, MeView, UserViewSet
from academics.views import DepartmentViewSet, CourseViewSet, SubjectViewSet, EnrollmentViewSet
from attendance.views import AttendanceViewSet
from communication.views import PostViewSet
from accounts.faculty_views import (
    FacultyAttendanceView,
    FacultyPostView,
    FacultySectionsView,
    FacultyStudentsView,
    FacultySubjectsView,
)
from accounts.academic_admin_views import (
    AdminAcademicOptionsView,
    AdminDepartmentView,
    AdminFacultyAssignmentDetailView,
    AdminFacultyAssignmentView,
    AdminProgramCreateView,
    AdminProgramDetailView,
    AdminStudentAcademicView,
)
from accounts.student_views import StudentProfileView, StudentAttendanceView, StudentPostView

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("departments", DepartmentViewSet)
router.register("courses", CourseViewSet)
router.register("subjects", SubjectViewSet)
router.register("enrollments", EnrollmentViewSet)
router.register("attendance", AttendanceViewSet)
router.register("posts", PostViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    # Admin
    path("api/admin/roles/", AdminRoleListView.as_view()),
    path("api/admin/academic-options/", AdminAcademicOptionsView.as_view()),
    path("api/admin/departments/", AdminDepartmentView.as_view()),
    path("api/admin/programs/", AdminProgramCreateView.as_view()),
    path("api/admin/programs/<int:pk>/", AdminProgramDetailView.as_view()),
    path("api/admin/students/<int:pk>/academic/", AdminStudentAcademicView.as_view()),
    path("api/admin/faculty-assignments/", AdminFacultyAssignmentView.as_view()),
    path("api/admin/faculty-assignments/<int:pk>/", AdminFacultyAssignmentDetailView.as_view()),
    # Faculty
    path("api/faculty/subjects/", FacultySubjectsView.as_view()),
    path("api/faculty/sections/", FacultySectionsView.as_view()),
    path("api/faculty/sections/<int:section_id>/students/", FacultyStudentsView.as_view()),
    path("api/faculty/students/", FacultyStudentsView.as_view()),
    path("api/faculty/attendance/", FacultyAttendanceView.as_view()),
    path("api/faculty/attendance/<int:pk>/", FacultyAttendanceView.as_view()),
    path("api/faculty/posts/", FacultyPostView.as_view()),
    # Student
    path("api/student/profile/", StudentProfileView.as_view()),
    path("api/student/attendance/", StudentAttendanceView.as_view()),
    path("api/student/posts/", StudentPostView.as_view()),
    path("api/", include(router.urls)),
]
