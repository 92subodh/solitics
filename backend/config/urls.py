from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import AdminRoleListView, AdminUserViewSet, MeView, UserViewSet
from academics.views import DepartmentViewSet, CourseViewSet, SubjectViewSet, EnrollmentViewSet
from attendance.views import AttendanceViewSet
from fees.views import FeeStructureViewSet, PaymentViewSet
from library.views import BookViewSet, LoanViewSet
from communication.views import NoticeViewSet, PostViewSet
from accounts.faculty_views import (
    FacultyAttendanceReportView,
    FacultyAttendanceView,
    FacultyDashboardView,
    FacultyExamsView,
    FacultyLeaveView,
    FacultyMarksReportView,
    FacultyMarksView,
    FacultyNoticeView,
    FacultyPostView,
    FacultyProfileView,
    FacultySectionsView,
    FacultyStudentsView,
    FacultySubjectsView,
    FacultyTimetableView,
)
from accounts.student_views import (
    StudentAcademicsView,
    StudentAttendanceView,
    StudentBooksView,
    StudentClubMembershipView,
    StudentClubsView,
    StudentDashboardView,
    StudentDocumentsView,
    StudentEventRegistrationView,
    StudentEventsView,
    StudentExamsView,
    StudentFeeSummaryView,
    StudentGradeCardsView,
    StudentInvoicesView,
    StudentLeaveView,
    StudentLibraryIssuesView,
    StudentLibraryReservationsView,
    StudentMarksView,
    StudentNoticesView,
    StudentNotificationsView,
    StudentPaymentsView,
    StudentPostsView,
    StudentPostInteractionView,
    StudentProfileView,
    StudentReceiptsView,
    StudentRequestsView,
    StudentResultsView,
    StudentSubjectsView,
    StudentTimetableView,
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

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("departments", DepartmentViewSet)
router.register("courses", CourseViewSet)
router.register("subjects", SubjectViewSet)
router.register("enrollments", EnrollmentViewSet)
router.register("attendance", AttendanceViewSet)
router.register("fee-structures", FeeStructureViewSet)
router.register("payments", PaymentViewSet)
router.register("books", BookViewSet)
router.register("loans", LoanViewSet)
router.register("notices", NoticeViewSet)
router.register("posts", PostViewSet)

urlpatterns = [
    path("admin/", admin.site.urls), path("api/auth/login/", TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()), path("api/auth/me/", MeView.as_view()),
    path("api/admin/roles/", AdminRoleListView.as_view()),
    path("api/admin/academic-options/", AdminAcademicOptionsView.as_view()),
    path("api/admin/departments/", AdminDepartmentView.as_view()),
    path("api/admin/programs/", AdminProgramCreateView.as_view()),
    path("api/admin/programs/<int:pk>/", AdminProgramDetailView.as_view()),
    path("api/admin/students/<int:pk>/academic/", AdminStudentAcademicView.as_view()),
    path("api/admin/faculty-assignments/", AdminFacultyAssignmentView.as_view()),
    path("api/admin/faculty-assignments/<int:pk>/", AdminFacultyAssignmentDetailView.as_view()),
    path("api/faculty/dashboard/", FacultyDashboardView.as_view()),
    path("api/faculty/profile/", FacultyProfileView.as_view()),
    path("api/faculty/subjects/", FacultySubjectsView.as_view()),
    path("api/faculty/sections/", FacultySectionsView.as_view()),
    path("api/faculty/sections/<int:section_id>/students/", FacultyStudentsView.as_view()),
    path("api/faculty/students/", FacultyStudentsView.as_view()),
    path("api/faculty/timetable/", FacultyTimetableView.as_view()),
    path("api/faculty/attendance/", FacultyAttendanceView.as_view()),
    path("api/faculty/attendance/<int:pk>/", FacultyAttendanceView.as_view()),
    path("api/faculty/attendance/reports/", FacultyAttendanceReportView.as_view()),
    path("api/faculty/exams/", FacultyExamsView.as_view()),
    path("api/faculty/marks/", FacultyMarksView.as_view()),
    path("api/faculty/marks/<int:pk>/", FacultyMarksView.as_view()),
    path("api/faculty/marks/reports/", FacultyMarksReportView.as_view()),
    path("api/faculty/posts/", FacultyPostView.as_view()),
    path("api/faculty/notices/", FacultyNoticeView.as_view()),
    path("api/faculty/leave-requests/", FacultyLeaveView.as_view()),
    path("api/student/dashboard/", StudentDashboardView.as_view()),
    path("api/student/profile/", StudentProfileView.as_view()),
    path("api/student/documents/", StudentDocumentsView.as_view()),
    path("api/student/academics/", StudentAcademicsView.as_view()),
    path("api/student/subjects/", StudentSubjectsView.as_view()),
    path("api/student/timetable/", StudentTimetableView.as_view()),
    path("api/student/attendance/", StudentAttendanceView.as_view()),
    path("api/student/attendance/<int:subject_id>/", StudentAttendanceView.as_view()),
    path("api/student/exams/", StudentExamsView.as_view()),
    path("api/student/marks/", StudentMarksView.as_view()),
    path("api/student/results/", StudentResultsView.as_view()),
    path("api/student/grade-cards/", StudentGradeCardsView.as_view()),
    path("api/student/fees/summary/", StudentFeeSummaryView.as_view()),
    path("api/student/fees/invoices/", StudentInvoicesView.as_view()),
    path("api/student/fees/payments/", StudentPaymentsView.as_view()),
    path("api/student/fees/receipts/", StudentReceiptsView.as_view()),
    path("api/student/fees/receipts/<int:pk>/", StudentReceiptsView.as_view()),
    path("api/student/library/books/", StudentBooksView.as_view()),
    path("api/student/library/issues/", StudentLibraryIssuesView.as_view()),
    path("api/student/library/issues/<int:pk>/renew/", StudentLibraryIssuesView.as_view()),
    path("api/student/library/reservations/", StudentLibraryReservationsView.as_view()),
    path("api/student/notices/", StudentNoticesView.as_view()),
    path("api/student/posts/", StudentPostsView.as_view()),
    path("api/student/posts/<int:pk>/interactions/", StudentPostInteractionView.as_view()),
    path("api/student/notifications/", StudentNotificationsView.as_view()),
    path("api/student/notifications/<int:pk>/", StudentNotificationsView.as_view()),
    path("api/student/leave/", StudentLeaveView.as_view()),
    path("api/student/requests/", StudentRequestsView.as_view()),
    path("api/student/events/", StudentEventsView.as_view()),
    path("api/student/events/<int:pk>/register/", StudentEventRegistrationView.as_view()),
    path("api/student/clubs/", StudentClubsView.as_view()),
    path("api/student/clubs/<int:pk>/join/", StudentClubMembershipView.as_view()),
    path("api/student/clubs/memberships/", StudentClubMembershipView.as_view()),
    path("api/", include(router.urls)),
]
