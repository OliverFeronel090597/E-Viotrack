
user_login_type = None

def is_admin():
    if user_login_type == "ADMIN":
        return 1
    else:
        return 0