from django.db import transaction
from rest_framework import serializers
from .models import Person, Role, User, UserRole, StudentProfile

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"
        read_only_fields = ("user",)

class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "phone", "is_active", "password", "student_profile")
        read_only_fields = ("id",)
    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password: user.set_password(password)
        user.save()
        return user
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items(): setattr(instance, field, value)
        if password: instance.set_password(password)
        instance.save()
        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="pk", read_only=True)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=User.Role.choices),
        required=True,
        allow_empty=False,
        write_only=True,
    )
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "user_id", "username", "email", "first_name", "last_name", "phone",
            "password", "roles", "is_active", "is_verified", "last_login", "date_joined",
        )
        read_only_fields = ("user_id", "last_login", "date_joined")

    def validate_roles(self, role_codes):
        existing = set(Role.objects.filter(role_code__in=role_codes).values_list("role_code", flat=True))
        missing = sorted(set(role_codes) - existing)
        if missing:
            raise serializers.ValidationError(f"Unknown role(s): {', '.join(missing)}")
        return list(dict.fromkeys(role_codes))

    def _sync_person(self, user, validated_data):
        if user.person_id:
            person = user.person
        else:
            person = Person.objects.create(first_name=user.first_name or user.username)
            user.person = person
            User.objects.filter(pk=user.pk).update(person=person)
        person.first_name = user.first_name
        person.last_name = user.last_name
        person.save(update_fields=("first_name", "last_name", "updated_at"))
        if user.person_id != person.pk:
            User.objects.filter(pk=user.pk).update(person=person)

    def _set_roles(self, user, role_codes):
        roles = Role.objects.filter(role_code__in=role_codes)
        UserRole.objects.filter(user=user).exclude(role__in=roles).delete()
        UserRole.objects.bulk_create(
            [UserRole(user=user, role=role) for role in roles],
            ignore_conflicts=True,
        )
        user.role = role_codes[0]
        user.save(update_fields=("role", "updated_at"))

    @transaction.atomic
    def create(self, validated_data):
        profile_data = self.initial_data.get("profile_data", {})
        role_codes = validated_data.pop("roles")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.role = role_codes[0]
        user.set_password(password)
        user.save()
        self._sync_person(user, validated_data)
        self._set_roles(user, role_codes)
        
        if "STUDENT" in role_codes:
            from .models import StudentProfile
            StudentProfile.objects.filter(user=user).update(
                admission_number=profile_data.get("admission_number") or None,
                current_roll_number=profile_data.get("roll_number") or None,
            )
        elif "FACULTY" in role_codes or "ADMIN" in role_codes:
            from .models import Employee
            Employee.objects.filter(user=user).update(
                employee_code=profile_data.get("employee_code") or None
            )
        
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        role_codes = validated_data.pop("roles", None)
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        self._sync_person(instance, validated_data)
        if role_codes is not None:
            self._set_roles(instance, role_codes)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        roles = list(instance.user_roles.select_related("role").values_list("role__role_code", flat=True))
        representation["roles"] = roles
        
        identifier = instance.username
        if hasattr(instance, "student_profile") and instance.student_profile:
            identifier = instance.student_profile.current_roll_number or instance.student_profile.admission_number or identifier
        elif hasattr(instance, "employee") and instance.employee:
            identifier = instance.employee.employee_code or identifier
            
        representation["identifier"] = identifier
        return representation
