from django.db import migrations


ROLE_NAMES = {
    "ADMIN": "Administrator",
    "FACULTY": "Faculty",
    "STUDENT": "Student",
    "PARENT": "Parent",
    "LIBRARIAN": "Librarian",
}


def seed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    UserRole = apps.get_model("accounts", "UserRole")

    roles = {
        code: Role.objects.get_or_create(role_code=code, defaults={"role_name": name})[0]
        for code, name in ROLE_NAMES.items()
    }
    for user in User.objects.all().only("id", "role"):
        role = roles.get(user.role)
        if role:
            UserRole.objects.get_or_create(user_id=user.pk, role_id=role.pk)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_backfill_identity_profiles")]
    operations = [migrations.RunPython(seed_roles, noop)]
