from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AdminProfile, Employee, FacultyProfile, LibrarianProfile, ParentProfile, Person, StudentProfile, User

@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return

    person = Person.objects.create(
        first_name=instance.first_name or instance.username,
        last_name=instance.last_name,
    )
    instance.person = person
    User.objects.filter(pk=instance.pk).update(person=person)
    if instance.role == User.Role.STUDENT:
        StudentProfile.objects.create(user=instance, admission_number=None)
    elif instance.role == User.Role.PARENT:
        ParentProfile.objects.create(user=instance, parent_code=f"PARENT-{instance.pk}")
    elif instance.role in (User.Role.ADMIN, User.Role.FACULTY, User.Role.LIBRARIAN):
        employee = Employee.objects.create(user=instance, employee_code=None)
        profile_model = {
            User.Role.ADMIN: AdminProfile,
            User.Role.FACULTY: FacultyProfile,
            User.Role.LIBRARIAN: LibrarianProfile,
        }[instance.role]
        profile_model.objects.create(employee=employee)
