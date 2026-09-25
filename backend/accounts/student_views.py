from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import ExamSubject, FacultySubject, ProgramSubject, StudentMark, StudentResult, Timetable
from attendance.models import AttendanceSession, LeaveRequest, StudentAttendance
from communication.models import (
    Club, ClubMembership, Event, EventRegistration, Notice, Notification, Post, PostComment, PostLike, ServiceRequest,
)
from fees.models import FeeInvoice, Payment, Receipt, StudentFeeAccount
from library.models import Book, BookIssue, LibraryFine, LibraryMember, LibraryReservation
from .models import StudentDocument, StudentProfile, User
from .student_serializers import (
    StudentClubMembershipSerializer,
    StudentDocumentSerializer,
    StudentEventRegistrationSerializer,
    StudentLeaveSerializer,
    StudentProfileSerializer,
    StudentServiceRequestSerializer,
)


class StudentAccessMixin:
    permission_classes = [IsAuthenticated]

    def get_student(self, request):
        user = request.user
        if not user.is_active or not user.user_roles.filter(role__role_code=User.Role.STUDENT).exists():
            raise PermissionDenied("An active STUDENT role is required.")
        try:
            return user.student_profile
        except StudentProfile.DoesNotExist:
            raise PermissionDenied("The authenticated user has no student profile.")

    def sections(self, request):
        return self.get_student(request).sections.all()


class StudentDashboardView(StudentAccessMixin, APIView):
    def get(self, request):
        student = self.get_student(request)
        attendance = StudentAttendance.objects.filter(student=student)
        total_attendance = attendance.count()
        present = attendance.filter(status__in=("PRESENT", "LATE")).count()
        fees = StudentFeeAccount.objects.filter(student=student).aggregate(total=Sum("total_amount"), paid=Sum("paid_amount"), pending=Sum("pending_amount"))
        library_member = LibraryMember.objects.filter(user=request.user).first()
        books_issued = BookIssue.objects.filter(library_member=library_member, return_date__isnull=True).count() if library_member else 0
        upcoming_exam = ExamSubject.objects.filter(
            subject__program_subjects__program_id=student.program_id,
            exam_date__gte=timezone.localdate(),
        ).select_related("exam", "subject").order_by("exam_date").first()
        return Response({
            "student": StudentProfileSerializer(student).data,
            "attendance": round((present / total_attendance) * 100, 2) if total_attendance else 0,
            "cgpa": StudentResult.objects.filter(student=student).order_by("-exam__end_date").values_list("cgpa", flat=True).first(),
            "pending_fees": fees["pending"] or 0,
            "books_issued": books_issued,
            "upcoming_exam": {"exam": upcoming_exam.exam.exam_name, "subject": upcoming_exam.subject.subject_name, "date": upcoming_exam.exam_date} if upcoming_exam else None,
            "new_notices": Notice.objects.filter(recipients__user=request.user, recipients__is_read=False).distinct().count(),
        })


class StudentProfileView(StudentAccessMixin, generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer

    def get_object(self):
        return self.get_student(self.request)


class StudentDocumentsView(StudentAccessMixin, generics.ListCreateAPIView):
    serializer_class = StudentDocumentSerializer

    def get_queryset(self):
        return StudentDocument.objects.filter(student=self.get_student(self.request)).order_by("-uploaded_at")

    def perform_create(self, serializer):
        serializer.save(student=self.get_student(self.request))


class StudentAcademicsView(StudentAccessMixin, APIView):
    def get(self, request):
        student = self.get_student(request)
        enrollment = student.enrollments.filter(active=True).select_related("program", "semester", "academic_year").order_by("-enrollment_date").first()
        section = student.sections.select_related("program", "semester", "academic_year").order_by("-section_id").first()
        program_subjects = ProgramSubject.objects.filter(
            program_id=student.program_id,
            semester__semester_number=student.current_semester,
        ).select_related("subject", "semester")
        return Response({
            "program": student.program.program_name if student.program else None,
            "department": student.department.department_name if student.department else None,
            "semester": student.current_semester,
            "section": section.section_code if section else None,
            "academic_year": enrollment.academic_year.year_code if enrollment and enrollment.academic_year else None,
            "subjects": [{"code": item.subject.subject_code, "name": item.subject.subject_name, "credits": item.subject.credits, "type": item.subject.subject_type} for item in program_subjects],
        })


class StudentSubjectsView(StudentAccessMixin, APIView):
    def get(self, request):
        student = self.get_student(request)
        assignments = FacultySubject.objects.filter(
            section__students=student,
            semester__semester_number=student.current_semester,
        ).select_related("subject", "faculty__employee__user")
        subjects = ProgramSubject.objects.filter(program_id=student.program_id, semester__semester_number=student.current_semester).select_related("subject")
        return Response([
            {
                "subject_id": item.subject_id,
                "subject_code": item.subject.subject_code,
                "subject_name": item.subject.subject_name,
                "credits": item.subject.credits,
                "faculty": [assignment.faculty.employee.user.display_name for assignment in assignments if assignment.subject_id == item.subject_id],
            }
            for item in subjects
        ])


class StudentTimetableView(StudentAccessMixin, APIView):
    def get(self, request):
        entries = Timetable.objects.filter(section__students=self.get_student(request)).select_related("subject", "faculty__employee__user", "room", "slot")
        if request.query_params.get("today") == "true":
            entries = entries.filter(slot__day_of_week=timezone.localdate().weekday())
        return Response([
            {"day": entry.slot.day_of_week, "start_time": entry.slot.start_time, "end_time": entry.slot.end_time, "subject": entry.subject.subject_name, "faculty": entry.faculty.employee.user.display_name, "room": entry.room.room_code}
            for entry in entries.order_by("slot__day_of_week", "slot__start_time")
        ])


class StudentAttendanceView(StudentAccessMixin, APIView):
    def get(self, request, subject_id=None):
        student = self.get_student(request)
        records = StudentAttendance.objects.filter(student=student).select_related("attendance_session__subject")
        if subject_id:
            records = records.filter(attendance_session__subject_id=subject_id)
        rows = [{"date": item.attendance_session.attendance_date, "subject": item.attendance_session.subject.subject_name, "subject_id": item.attendance_session.subject_id, "status": item.status} for item in records.order_by("-attendance_session__attendance_date")]
        total = len(rows)
        attended = sum(row["status"] in ("PRESENT", "LATE") for row in rows)
        return Response({"overall_percentage": round(attended * 100 / total, 2) if total else 0, "total": total, "attended": attended, "history": rows})


class StudentExamsView(StudentAccessMixin, APIView):
    def get(self, request):
        student = self.get_student(request)
        exams = ExamSubject.objects.filter(subject__program_subjects__program_id=student.program_id).select_related("exam", "subject").order_by("exam_date")
        return Response([{"exam_subject_id": item.exam_subject_id, "exam": item.exam.exam_name, "subject": item.subject.subject_name, "date": item.exam_date, "max_marks": item.max_marks, "passing_marks": item.passing_marks} for item in exams])


class StudentMarksView(StudentAccessMixin, APIView):
    def get(self, request):
        marks = StudentMark.objects.filter(student=self.get_student(request)).select_related("exam_subject__exam", "exam_subject__subject")
        return Response([{"marks_id": mark.marks_id, "exam": mark.exam_subject.exam.exam_name, "subject": mark.exam_subject.subject.subject_name, "marks_obtained": mark.marks_obtained, "internal_marks": mark.internal_marks, "practical_marks": mark.practical_marks} for mark in marks])


class StudentResultsView(StudentAccessMixin, APIView):
    def get(self, request):
        results = StudentResult.objects.filter(student=self.get_student(request)).select_related("exam")
        return Response([{"result_id": result.result_id, "exam": result.exam.exam_name, "percentage": result.percentage, "sgpa": result.sgpa, "cgpa": result.cgpa, "status": result.result_status} for result in results])


class StudentGradeCardsView(StudentAccessMixin, APIView):
    def get(self, request):
        cards = self.get_student(request).grade_cards.all()
        return Response([{"grade_card_id": card.grade_card_id, "exam": card.exam.exam_name, "certificate_number": card.certificate_number, "issue_date": card.issue_date, "pdf_url": card.pdf_url} for card in cards])


class StudentFeeSummaryView(StudentAccessMixin, APIView):
    def get(self, request):
        summary = StudentFeeAccount.objects.filter(student=self.get_student(request)).aggregate(total=Sum("total_amount"), paid=Sum("paid_amount"), pending=Sum("pending_amount"))
        next_due = FeeInvoice.objects.filter(fee_account__student=self.get_student(request), status__in=("PENDING", "PARTIAL")).order_by("due_date").values_list("due_date", flat=True).first()
        return Response({"total": summary["total"] or 0, "paid": summary["paid"] or 0, "pending": summary["pending"] or 0, "next_due_date": next_due})


class StudentInvoicesView(StudentAccessMixin, APIView):
    def get(self, request):
        invoices = FeeInvoice.objects.filter(fee_account__student=self.get_student(request)).prefetch_related("items__fee_category")
        return Response([{"invoice_id": invoice.invoice_id, "invoice_number": invoice.invoice_number, "invoice_date": invoice.invoice_date, "due_date": invoice.due_date, "total_amount": invoice.total_amount, "status": invoice.status, "items": [{"category": item.fee_category.category_name, "amount": item.amount} for item in invoice.items.all()]} for invoice in invoices])


class StudentPaymentsView(StudentAccessMixin, APIView):
    def get(self, request):
        payments = Payment.objects.filter(student_profile=self.get_student(request)).order_by("-id")
        return Response([{"payment_id": payment.pk, "invoice": payment.invoice.invoice_number if payment.invoice else None, "amount": payment.amount, "status": payment.status, "paid_at": payment.paid_at, "reference": payment.reference} for payment in payments])

    @transaction.atomic
    def post(self, request):
        student = self.get_student(request)
        invoice = get_object_or_404(FeeInvoice, pk=request.data.get("invoice"), fee_account__student=student)
        payment = Payment.objects.create(student=student.user, student_profile=student, invoice=invoice, amount=invoice.total_amount, status=Payment.Status.PENDING)
        return Response({"payment_id": payment.pk, "invoice": invoice.invoice_number, "amount": payment.amount, "status": payment.status}, status=status.HTTP_201_CREATED)


class StudentReceiptsView(StudentAccessMixin, APIView):
    def get(self, request, pk=None):
        receipts = Receipt.objects.filter(payment__student_profile=self.get_student(request))
        if pk:
            receipts = receipts.filter(pk=pk)
        return Response([{"receipt_id": receipt.receipt_id, "receipt_number": receipt.receipt_number, "receipt_url": receipt.receipt_url, "generated_at": receipt.generated_at} for receipt in receipts])


class StudentBooksView(StudentAccessMixin, APIView):
    def get(self, request):
        books = Book.objects.all().select_related("category")
        query = request.query_params.get("search")
        if query:
            books = books.filter(title__icontains=query) | books.filter(author__icontains=query) | books.filter(isbn__icontains=query)
        return Response([{"book_id": book.pk, "title": book.title, "author": book.author, "isbn": book.isbn, "available": book.copies_available} for book in books.distinct()])


class StudentLibraryIssuesView(StudentAccessMixin, APIView):
    def get_member(self, request):
        return LibraryMember.objects.filter(user=request.user, active=True).first()

    def get(self, request):
        member = self.get_member(request)
        issues = BookIssue.objects.filter(library_member=member).select_related("copy__book") if member else BookIssue.objects.none()
        return Response([{"issue_id": issue.issue_id, "book": issue.copy.book.title, "due_date": issue.due_date, "return_date": issue.return_date, "status": issue.status} for issue in issues])

    @transaction.atomic
    def post(self, request, pk=None):
        member = self.get_member(request)
        if not member:
            raise ValidationError("You do not have an active library membership.")
        issue = get_object_or_404(BookIssue, pk=pk, library_member=member, return_date__isnull=True)
        issue.due_date = issue.due_date + timedelta(days=7)
        issue.status = "RENEWED"
        issue.save(update_fields=("due_date", "status"))
        return Response({"issue_id": issue.issue_id, "due_date": issue.due_date, "status": issue.status})


class StudentLibraryReservationsView(StudentAccessMixin, APIView):
    def get(self, request):
        member = LibraryMember.objects.filter(user=request.user, active=True).first()
        reservations = LibraryReservation.objects.filter(library_member=member).select_related("book") if member else LibraryReservation.objects.none()
        return Response([{"reservation_id": item.reservation_id, "book": item.book.title, "status": item.status, "reserved_at": item.reservation_date} for item in reservations])

    def post(self, request):
        member = LibraryMember.objects.filter(user=request.user, active=True).first()
        if not member:
            raise ValidationError("You do not have an active library membership.")
        book = get_object_or_404(Book, pk=request.data.get("book"))
        reservation, created = LibraryReservation.objects.get_or_create(book=book, library_member=member, status="ACTIVE")
        return Response({"reservation_id": reservation.reservation_id, "status": reservation.status}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class StudentNoticesView(StudentAccessMixin, APIView):
    def get(self, request):
        notices = Notice.objects.filter(recipients__user=request.user).distinct().order_by("-published_at")
        return Response([{"notice_id": notice.pk, "title": notice.title, "body": notice.body, "published_at": notice.published_at} for notice in notices])


class StudentPostsView(StudentAccessMixin, APIView):
    def get(self, request):
        student = self.get_student(request)
        visibility = ["ALL"] + [f"SECTION:{section_id}" for section_id in student.sections.values_list("section_id", flat=True)]
        posts = Post.objects.filter(visibility__in=visibility).order_by("-created_at")
        return Response([{"post_id": post.post_id, "title": post.title, "content": post.content, "created_at": post.created_at} for post in posts])


class StudentPostInteractionView(StudentAccessMixin, APIView):
    def post(self, request, pk=None):
        student = self.get_student(request)
        post = get_object_or_404(Post, pk=pk)
        comment = PostComment.objects.create(post=post, user=request.user, content=request.data.get("content", ""))
        return Response({"comment_id": comment.comment_id, "content": comment.content}, status=status.HTTP_201_CREATED)

    def put(self, request, pk=None):
        student = self.get_student(request)
        post = get_object_or_404(Post, pk=pk)
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
        return Response({"liked": created})


class StudentNotificationsView(StudentAccessMixin, APIView):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
        return Response([{"notification_id": item.notification_id, "title": item.title, "message": item.message, "is_read": item.is_read, "created_at": item.created_at} for item in notifications])

    def patch(self, request, pk=None):
        notification = get_object_or_404(Notification, pk=pk, user=self.get_student(request).user)
        notification.is_read = True
        notification.save(update_fields=("is_read",))
        return Response({"notification_id": notification.notification_id, "is_read": True})


class StudentLeaveView(StudentAccessMixin, generics.ListCreateAPIView):
    serializer_class = StudentLeaveSerializer

    def get_queryset(self):
        return LeaveRequest.objects.filter(user=self.get_student(self.request).user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.get_student(self.request).user)


class StudentRequestsView(StudentAccessMixin, generics.ListCreateAPIView):
    serializer_class = StudentServiceRequestSerializer

    def get_queryset(self):
        return ServiceRequest.objects.filter(student=self.get_student(self.request)).order_by("-submitted_at")

    def perform_create(self, serializer):
        serializer.save(student=self.get_student(self.request))


class StudentEventsView(StudentAccessMixin, APIView):
    def get(self, request):
        events = Event.objects.filter(is_active=True).order_by("start_at")
        return Response([{"event_id": event.event_id, "name": event.name, "description": event.description, "start_at": event.start_at, "end_at": event.end_at, "venue": event.venue, "capacity": event.capacity} for event in events])


class StudentEventRegistrationView(StudentAccessMixin, APIView):
    def post(self, request, pk=None):
        event = get_object_or_404(Event, pk=pk, is_active=True)
        registration, created = EventRegistration.objects.get_or_create(event=event, student=self.get_student(request))
        return Response({"event": event.event_id, "status": registration.status}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, pk=None):
        registration = get_object_or_404(EventRegistration, event_id=pk, student=self.get_student(request))
        registration.status = "CANCELLED"
        registration.save(update_fields=("status",))
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudentClubsView(StudentAccessMixin, APIView):
    def get(self, request):
        clubs = Club.objects.filter(is_active=True).order_by("name")
        return Response([{"club_id": club.club_id, "name": club.name, "description": club.description} for club in clubs])


class StudentClubMembershipView(StudentAccessMixin, APIView):
    def post(self, request, pk=None):
        club = get_object_or_404(Club, pk=pk, is_active=True)
        membership, created = ClubMembership.objects.get_or_create(club=club, student=self.get_student(request))
        return Response({"club": club.club_id, "status": membership.status}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def get(self, request):
        memberships = ClubMembership.objects.filter(student=self.get_student(request)).select_related("club")
        return Response([{"club_id": membership.club_id, "name": membership.club.name, "status": membership.status} for membership in memberships])
