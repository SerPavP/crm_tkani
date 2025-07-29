from django.contrib.auth.models import User

# username: новый пароль
passwords = {
    'admin': 'gg312552',
    'accountant': 'buh116622',
    'warehouse': 'scr1f55',
}

for username, new_password in passwords.items():
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f"Пароль для пользователя {username} успешно изменён.")
    except User.DoesNotExist:
        print(f"Пользователь {username} не найден.")
