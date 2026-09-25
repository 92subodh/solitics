from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from accounts.models import User
from .models import Book, Loan
from .serializers import BookSerializer, LoanSerializer

def is_librarian(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.role in (User.Role.ADMIN, User.Role.LIBRARIAN)))

class LibraryInventoryPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_librarian(request.user)

class LoanPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        if request.method == "DELETE":
            return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.role == User.Role.ADMIN))
        return is_librarian(request.user)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [LibraryInventoryPermission]

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.select_related("book", "borrower").all()
    serializer_class = LoanSerializer
    permission_classes = [LoanPermission]

    @transaction.atomic
    def perform_create(self, serializer):
        book = Book.objects.select_for_update().get(pk=serializer.validated_data["book"].pk)
        borrower = serializer.validated_data["borrower"]
        if book.copies_available < 1:
            raise ValidationError({"book": "No copies of this book are available."})
        if Loan.objects.filter(book=book, borrower=borrower, returned_on__isnull=True).exists():
            raise ValidationError({"book": "This borrower already has an active loan for this book."})
        book.copies_available -= 1
        book.save(update_fields=["copies_available"])
        serializer.save(book=book)

    @action(detail=True, methods=["post"], url_path="return-book")
    @transaction.atomic
    def return_book(self, request, pk=None):
        loan = self.get_object()
        if loan.returned_on:
            raise ValidationError({"detail": "This loan has already been returned."})
        book = Book.objects.select_for_update().get(pk=loan.book_id)
        loan.returned_on = timezone.localdate()
        loan.save(update_fields=["returned_on"])
        book.copies_available = min(book.copies_available + 1, book.copies_total)
        book.save(update_fields=["copies_available"])
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"])
    def reissue(self, request, pk=None):
        loan = self.get_object()
        if loan.returned_on:
            raise ValidationError({"detail": "A returned loan cannot be reissued."})
        due_on = request.data.get("due_on")
        if not due_on:
            raise ValidationError({"due_on": "Provide a new due date in YYYY-MM-DD format."})
        serializer = self.get_serializer(loan, data={"due_on": due_on}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
