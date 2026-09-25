from rest_framework import viewsets
from accounts.permissions import IsAdminOrReadOnly
from .models import FeeStructure, Payment
from .serializers import FeeStructureSerializer, PaymentSerializer
class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.select_related("course").all(); serializer_class = FeeStructureSerializer; permission_classes = [IsAdminOrReadOnly]
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("student", "fee_structure").all(); serializer_class = PaymentSerializer; permission_classes = [IsAdminOrReadOnly]
