from rest_framework import serializers
from .models import Book, Loan
class BookSerializer(serializers.ModelSerializer):
    class Meta: model = Book; fields = "__all__"
class LoanSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    class Meta: model = Loan; fields = "__all__"
