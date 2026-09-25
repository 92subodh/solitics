from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import ERPUserChangeForm, ERPUserCreationForm
from .models import AdminProfile, FacultyProfile, StudentProfile, User


@admin.register(User)
class ERPUserAdmin(UserAdmin):
    add_form = ERPUserCreationForm
    form = ERPUserChangeForm
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    fieldsets = (
        ("Login credentials", {"fields": ("username", "password")}),
        ("Personal details", {"fields": ("first_name", "last_name", "email", "phone")}),
        ("ERP role", {"fields": ("role",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        ("Create ERP user", {"classes": ("wide",), "fields": ("username", "email", "first_name", "last_name", "role", "phone", "password1", "password2", "is_active", "is_staff", "is_superuser")}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("roll_number", "user", "guardian_name", "guardian_phone")
    search_fields = ("current_roll_number", "user__username", "user__first_name", "user__last_name")


admin.site.register(FacultyProfile)
admin.site.register(AdminProfile)
