from django.contrib.auth.hashers import make_password
from passenger.models import User 

def run():
    print("Running create_admin script...")
    if not User.objects.filter(email='admin@example.com').exists():
        User.objects.create(
            first_name='Saif',
            last_name='Admin',
            email='admin@example.com',
            phone='1234567890',
            password=make_password('admin@123'),
            country_code='+91',
            is_admin=True,
            is_staff=True,
            is_active=True
        )
        print("✅ Admin user created.")
    else:
        print("⚠️ Admin already exists.")
        
if __name__ == '__main__' or True:
    run()