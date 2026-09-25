from django.db import migrations


def backfill_identity_profiles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Person = apps.get_model("accounts", "Person")
    StudentProfile = apps.get_model("accounts", "StudentProfile")
    ParentProfile = apps.get_model("accounts", "ParentProfile")
    Employee = apps.get_model("accounts", "Employee")
    AdminProfile = apps.get_model("accounts", "AdminProfile")
    FacultyProfile = apps.get_model("accounts", "FacultyProfile")
    LibrarianProfile = apps.get_model("accounts", "LibrarianProfile")

    for user in User.objects.all().iterator():
        person = Person.objects.create(
            first_name=user.first_name or user.username,
            last_name=user.last_name,
        )
        User.objects.filter(pk=user.pk).update(person_id=person.pk)

        if user.role == "STUDENT":
            StudentProfile.objects.create(user_id=user.pk, admission_number=f"MIGRATED-{user.pk}")
        elif user.role == "PARENT":
            ParentProfile.objects.create(user_id=user.pk, parent_code=f"MIGRATED-PARENT-{user.pk}")
        elif user.role in {"ADMIN", "FACULTY", "LIBRARIAN"}:
            employee = Employee.objects.create(user_id=user.pk, employee_code=f"MIGRATED-EMP-{user.pk}")
            profile_model = {
                "ADMIN": AdminProfile,
                "FACULTY": FacultyProfile,
                "LIBRARIAN": LibrarianProfile,
            }[user.role]
            profile_model.objects.create(employee_id=employee.pk)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_address_permission_person_role_and_more")]
    operations = [migrations.RunPython(backfill_identity_profiles, noop)]
