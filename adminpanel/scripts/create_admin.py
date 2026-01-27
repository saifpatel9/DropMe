from adminpanel.models import AdminUser

def run():
    if not AdminUser.objects.filter(email="admin@dropme.com").exists():
        AdminUser.objects.create_superuser(
            email="admin@dropme.com",
            name="Super Admin",
            phone="9999999999",
            password="Admin@123"
        )
        print("✅ AdminUser created")
    else:
        print("⚠️ AdminUser already exists")
