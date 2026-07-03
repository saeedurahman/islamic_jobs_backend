from django.core.management.base import BaseCommand

from profiles.models import Language

LANGUAGES = [
    {'name': 'Urdu', 'name_urdu': 'اردو'},
    {'name': 'English', 'name_urdu': 'انگریزی'},
    {'name': 'Arabic', 'name_urdu': 'عربی'},
    {'name': 'Punjabi', 'name_urdu': 'پنجابی'},
    {'name': 'Sindhi', 'name_urdu': 'سندھی'},
    {'name': 'Pashto', 'name_urdu': 'پشتو'},
    {'name': 'Balochi', 'name_urdu': 'بلوچی'},
    {'name': 'Saraiki', 'name_urdu': 'سرائیکی'},
]


class Command(BaseCommand):
    help = 'Seed reference languages for profiles (idempotent).'

    def handle(self, *args, **options):
        created_count = 0
        for language_data in LANGUAGES:
            _, created = Language.objects.get_or_create(
                name=language_data['name'],
                defaults={'name_urdu': language_data['name_urdu']},
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created language: {language_data["name"]}')
        self.stdout.write(
            self.style.SUCCESS(f'Seed complete: {created_count} language(s) created.')
        )
