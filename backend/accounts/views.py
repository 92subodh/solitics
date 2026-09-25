from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Role, User
from .permissions import IsAdminOrReadOnly
from .serializers import AdminUserSerializer, UserSerializer


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    def get_object(self): return self.request.user

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]


class AdminUserViewSet(viewsets.ModelViewSet):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = User.objects.select_related("person").prefetch_related("user_roles__role").order_by("username")
        params = self.request.query_params
        role = params.get("role")
        status_value = params.get("status")
        search = params.get("name") or params.get("search")
        email = params.get("email")
        if role:
            queryset = queryset.filter(user_roles__role__role_code=role.upper())
        if status_value:
            queryset = queryset.filter(is_active=status_value.lower() in ("active", "true", "1"))
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(person__first_name__icontains=search)
                | Q(person__last_name__icontains=search)
                | Q(username__icontains=search)
            )
        if email:
            queryset = queryset.filter(email__icontains=email)
        return queryset.distinct()

    def _is_admin(self, user):
        return bool(
            user.is_authenticated
            and user.is_active
            and user.user_roles.filter(role__role_code=User.Role.ADMIN).exists()
        )

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not self._is_admin(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("An active ADMIN role is required.")

    @transaction.atomic
    def perform_create(self, serializer):
        user = serializer.save()

    @transaction.atomic
    def perform_update(self, serializer):
        target = self.get_object()
        user = serializer.save()

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.user_roles.filter(role__role_code=User.Role.ADMIN).exists():
            return Response(
                {"detail": "Administrator accounts cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="status")
    def status(self, request, pk=None):
        user = self.get_object()
        is_active = request.data.get("is_active")
        if not isinstance(is_active, bool):
            return Response({"is_active": "This field must be a boolean."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = is_active
        user.save(update_fields=("is_active", "updated_at"))
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["patch"], url_path="roles")
    def roles(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user, data={"roles": request.data.get("roles")}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("new_password")
        if not isinstance(new_password, str) or len(new_password) < 8:
            return Response({"new_password": "Use at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=("password", "updated_at"))
        return Response({"detail": "Password reset successfully."})


class AdminRoleListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        return Role.objects.all().order_by("role_code")

    def list(self, request, *args, **kwargs):
        if not request.user.is_active or not (
            request.user.user_roles.filter(role__role_code=User.Role.ADMIN).exists()
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("An active ADMIN role is required.")
        return Response([{"role_code": role.role_code, "role_name": role.role_name} for role in self.get_queryset()])
