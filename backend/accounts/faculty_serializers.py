from rest_framework import serializers

from academics.models import FacultySubject
from attendance.models import LeaveRequest, StudentAttendance
from communication.models import Notice, Post
from .models import Address, FacultyProfile, Person, PersonAddress, User


class FacultyAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("address_line1", "address_line2", "city", "state", "country", "postal_code")


class FacultyProfileSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source="employee.employee_code", read_only=True)
    department = serializers.CharField(source="department.department_name", read_only=True)
    designation = serializers.CharField(source="employee.designation", read_only=True)
    email = serializers.EmailField(source="employee.user.email", read_only=True)
    phone = serializers.CharField(source="employee.user.phone", required=False)
    profile_photo = serializers.URLField(source="employee.user.person.profile_photo", required=False, allow_blank=True)
    address = FacultyAddressSerializer(write_only=True, required=False)

    class Meta:
        model = FacultyProfile
        fields = (
            "employee_id", "department", "designation", "specialization", "qualification",
            "experience_years", "email", "phone", "profile_photo", "address",
        )
        read_only_fields = ("employee_id", "department", "designation", "specialization", "qualification", "experience_years", "email")

    def update(self, instance, validated_data):
        employee_data = validated_data.pop("employee", {})
        user_data = employee_data.get("user", {})
        person_data = user_data.get("person", {})
        address_data = validated_data.pop("address", None)
        phone = user_data.get("phone")
        profile_photo = person_data.get("profile_photo")
        if phone is not None:
            instance.employee.user.phone = phone
            instance.employee.user.save(update_fields=("phone", "updated_at"))
        if profile_photo is not None and instance.employee.user.person:
            instance.employee.user.person.profile_photo = profile_photo
            instance.employee.user.person.save(update_fields=("profile_photo", "updated_at"))
        if address_data:
            person = instance.employee.user.person
            address_link = person.addresses.filter(address_type="HOME", is_primary=True).select_related("address").first()
            if address_link:
                for field, value in address_data.items():
                    setattr(address_link.address, field, value)
                address_link.address.save()
            else:
                address = Address.objects.create(**address_data)
                PersonAddress.objects.create(person=person, address=address, address_type="HOME", is_primary=True)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        person = instance.employee.user.person
        home_address = person.addresses.filter(address_type="HOME", is_primary=True).first() if person else None
        representation["address"] = FacultyAddressSerializer(home_address.address).data if home_address else None
        return representation


class FacultySubjectSerializer(serializers.ModelSerializer):
    subject_code = serializers.CharField(source="subject.subject_code", read_only=True)
    subject_name = serializers.CharField(source="subject.subject_name", read_only=True)
    semester_number = serializers.IntegerField(source="semester.semester_number", read_only=True)
    section_code = serializers.CharField(source="section.section_code", read_only=True)
    academic_year_code = serializers.CharField(source="academic_year.year_code", read_only=True)

    class Meta:
        model = FacultySubject
        fields = (
            "faculty_subject_id", "subject", "subject_code", "subject_name", "semester",
            "semester_number", "section", "section_code", "academic_year", "academic_year_code",
        )
        read_only_fields = fields


class StudentAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttendance
        fields = "__all__"
        read_only_fields = ("marked_at",)


class FacultyMarkSerializer(serializers.Serializer):
    exam_subject = serializers.IntegerField()
    student = serializers.IntegerField()
    marks_obtained = serializers.DecimalField(max_digits=7, decimal_places=2)
    internal_marks = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, default=0)
    practical_marks = serializers.DecimalField(max_digits=7, decimal_places=2, required=False, default=0)
    remarks = serializers.CharField(required=False, allow_blank=True)


class FacultyLeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ("leave_request_id", "leave_type", "start_date", "end_date", "reason", "status", "created_at")
        read_only_fields = ("leave_request_id", "status", "created_at")


class FacultyPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("post_id", "title", "content", "image_url", "visibility", "created_at")
        read_only_fields = ("post_id", "created_at")


class FacultyNoticeSerializer(serializers.ModelSerializer):
    section = serializers.IntegerField(write_only=True)

    class Meta:
        model = Notice
        fields = ("id", "title", "body", "section", "published_at")
        read_only_fields = ("id", "published_at")

    def create(self, validated_data):
        validated_data.pop("section", None)
        return Notice.objects.create(**validated_data)
