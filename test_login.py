from getpass import getpass

from db_supabase import get_supabase

email = input("Smart Journal email: ").strip()
password = getpass("Password: ")

client = get_supabase()

try:
    result = client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    print("Login successful.")
    print("User ID:", result.user.id)
except Exception as error:
    print("Login failed:", error)
