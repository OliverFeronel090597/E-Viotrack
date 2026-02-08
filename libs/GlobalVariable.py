
user_login_type = "ADMIN"

def is_admin():
    if user_login_type == "ADMIN":
        return 1
    else:
        return 0