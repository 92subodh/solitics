from django.conf import settings
from django.db import models
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey("library.BookCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    publisher = models.ForeignKey("library.Publisher", on_delete=models.SET_NULL, null=True, blank=True, related_name="books")
    edition = models.CharField(max_length=50, blank=True)
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, blank=True)
    copies_total = models.PositiveIntegerField(default=1)
    copies_available = models.PositiveIntegerField(default=1)
    def __str__(self): return self.title
class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="loans")
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="book_loans")
    issued_on = models.DateField(auto_now_add=True)
    due_on = models.DateField()
    returned_on = models.DateField(null=True, blank=True)
    class Meta: ordering = ("-issued_on",)

    @property
    def is_active(self):
        return self.returned_on is None


class BookCategory(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_code = models.CharField(max_length=30, unique=True)
    category_name = models.CharField(max_length=100)


class Author(models.Model):
    author_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    biography = models.TextField(blank=True)


class Publisher(models.Model):
    publisher_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=100, blank=True)


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="authors")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("book", "author"), name="unique_book_author")]


class BookCopy(models.Model):
    copy_id = models.BigAutoField(primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    accession_number = models.CharField(max_length=50, unique=True)
    shelf_location = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=30, default="AVAILABLE")


class LibraryMember(models.Model):
    library_member_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="library_membership")
    membership_number = models.CharField(max_length=50, unique=True)
    issue_limit = models.PositiveSmallIntegerField(default=3)
    active = models.BooleanField(default=True)


class BookIssue(models.Model):
    issue_id = models.BigAutoField(primary_key=True)
    copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name="issues")
    library_member = models.ForeignKey(LibraryMember, on_delete=models.PROTECT, related_name="issues")
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, default="ISSUED")


class LibraryReservation(models.Model):
    reservation_id = models.BigAutoField(primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
    library_member = models.ForeignKey(LibraryMember, on_delete=models.CASCADE, related_name="reservations")
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, default="ACTIVE")


class LibraryFine(models.Model):
    fine_id = models.BigAutoField(primary_key=True)
    issue = models.ForeignKey(BookIssue, on_delete=models.CASCADE, related_name="fines")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=30, default="UNPAID")
