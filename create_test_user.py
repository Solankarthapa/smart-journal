from getpass import getpass

from db_supabase import get_supabase

email = input("Email for Smart Journal test account: ").strip()
password = getpass("Password: ")

client = get_supabase()

try:
    result = client.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )
    print("User created.")
    print("Confirmation required:", result.session is None)
except Exception as error:
    print("Could not create user:", error)
