import getpass

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from accounts.utils import generate_username, is_valid_pakistani_phone, normalize_phone_number


class Command(BaseCommand):
    help = 'Create or promote a user to platform admin (user_role=admin, is_staff=True).'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address for the admin user.')

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        user = User.objects.filter(email__iexact=email).first()

        password = getpass.getpass('Password: ')
        password_confirm = getpass.getpass('Confirm password: ')
        if password != password_confirm:
            raise CommandError('Passwords do not match.')
        if not password:
            raise CommandError('Password cannot be empty.')

        if user:
            if user.user_role == User.Role.ADMIN and user.is_staff:
                confirm = input(
                    f'User {email} is already an admin. Update password? [y/N]: '
                ).strip().lower()
                if confirm != 'y':
                    self.stdout.write(self.style.WARNING('Aborted.'))
                    return
            else:
                confirm = input(
                    f'User {email} exists with role "{user.user_role}". '
                    f'Promote to admin? [y/N]: '
                ).strip().lower()
                if confirm != 'y':
                    self.stdout.write(self.style.WARNING('Aborted.'))
                    return
            user.user_role = User.Role.ADMIN
            user.is_staff = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated admin user: {email}'))
        else:
            phone = input('Phone number (03XXXXXXXXX or +92...): ').strip()
            normalized_phone = normalize_phone_number(phone)
            if not is_valid_pakistani_phone(normalized_phone):
                raise CommandError('Invalid Pakistani phone number.')
            if User.objects.filter(phone_number=normalized_phone).exists():
                raise CommandError('Phone number is already registered.')

            user = User(
                username=generate_username(email),
                email=email,
                phone_number=normalized_phone,
                user_role=User.Role.ADMIN,
                is_staff=True,
            )
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {email}'))

        self.stdout.write('This account can use /api/v1/admin/ endpoints and Django /admin/.')
