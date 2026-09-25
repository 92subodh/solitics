from rest_framework import serializers

from accounts.models import Address, PersonAddress, StudentDocument, StudentProfile
from communication.models import ClubMembership, EventRegistration, ServiceRequest
from attendance.models import LeaveRequest


class StudentProfileSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    admission_number = serializers.CharField(read_only=True)
    roll_number = serializers.CharField(source="current_roll_number", read_only=True)
    department = serializers.CharField(read_only=True)
    program = serializers.CharField(read_only=True)
    semester = serializers.IntegerField(source="current_semester", read_only=True)
    section = serializers.CharField(read_only=True)
    date_of_birth = serializers.DateField(source="user.person.date_of_birth", read_only=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    profile_photo = serializers.URLField(required=False, allow_blank=True)
    address = serializers.DictField(required=False)
    emergency_contact = serializers.CharField(required=False, allow_blank=True)

    def to_representation(self, instance):
        person = instance.user.person
        section = instance.sections.order_by("section_id").first()
        home = person.addresses.filter(address_type="HOME", is_primary=True).select_related("address").first() if person else None
        return {
            "student_id": instance.student_id,
            "name": instance.user.display_name,
            "admission_number": instance.admission_number,
            "roll_number": instance.current_roll_number,
            "department": instance.department.department_name if instance.department else None,
            "program": instance.program.program_name if instance.program else None,
            "semester": instance.current_semester,
            "section": section.section_code if section else None,
            "date_of_birth": person.date_of_birth if person else None,
            "email": instance.user.email,
            "phone": instance.user.phone,
            "profile_photo": person.profile_photo if person else "",
            "address": {
                field: getattr(home.address, field)
                for field in ("address_line1", "address_line2", "city", "state", "country", "postal_code")
            } if home else None,
            "emergency_contact": instance.guardian_phone,
        }

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        if "email" in validated_data:
            instance.user.email = validated_data["email"]
        if "phone" in validated_data:
            instance.user.phone = validated_data["phone"]
        instance.user.save(update_fields=("email", "phone", "updated_at"))
        if instance.user.person:
            if "profile_photo" in validated_data:
                instance.user.person.profile_photo = validated_data["profile_photo"]
                instance.user.person.save(update_fields=("profile_photo", "updated_at"))
            if address_data:
                link = instance.user.person.addresses.filter(address_type="HOME", is_primary=True).select_related("address").first()
                if link:
                    for field, value in address_data.items():
                        setattr(link.address, field, value)
                    link.address.save()
                else:
                    address = Address.objects.create(**address_data)
                    PersonAddress.objects.create(person=instance.user.person, address=address, address_type="HOME", is_primary=True)
        if "emergency_contact" in validated_data:
            instance.guardian_phone = validated_data["emergency_contact"]
            instance.save(update_fields=("guardian_phone",))
        return instance


class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = ("document_id", "document_type", "file_url", "status", "uploaded_at", "verified_at")
        read_only_fields = ("document_id", "status", "uploaded_at", "verified_at")


class StudentLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ("leave_request_id", "leave_type", "start_date", "end_date", "reason", "status", "created_at")
        read_only_fields = ("leave_request_id", "status", "created_at")


class StudentServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = ("request_id", "request_type", "description", "status", "response", "submitted_at", "updated_at")
        read_only_fields = ("request_id", "status", "response", "submitted_at", "updated_at")


class StudentEventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ("event", "status", "registered_at")
        read_only_fields = ("status", "registered_at")


class StudentClubMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubMembership
        fields = ("club", "status", "joined_at")
        read_only_fields = ("status", "joined_at")
