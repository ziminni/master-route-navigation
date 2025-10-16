from django.contrib.auth.models import Group

# Sample code to manipulate group membership
class OrgOfficer:
    def grant(user):
        group, _ = Group.objects.get_or_create(name="org_officer")
        user.groups.add(group)

    def revoke(user):
        group, _ = Group.objects.get_or_create(name="org_officer")
        user.groups.remove(group)

class Registrar:
    def grant(user):
        group, _ = Group.objects.get_or_create(name="registrar")
        user.groups.add(group)
    def revoke(user):
        group, _ = Group.objects.get_or_create(name="registrar")
        user.groups.remove(group)
