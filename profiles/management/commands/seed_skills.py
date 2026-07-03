from django.core.management.base import BaseCommand

from profiles.models import Skill

SKILLS = [
    {'name': 'MS Office', 'name_urdu': 'ایم ایس آفس'},
    {'name': 'Teaching', 'name_urdu': 'تدریس'},
    {'name': 'Public Speaking', 'name_urdu': 'عوامی تقریر'},
    {'name': 'Management', 'name_urdu': 'انتظامیہ'},
    {'name': 'Counselling', 'name_urdu': 'مشاورت'},
    {'name': 'Research', 'name_urdu': 'تحقیق'},
    {'name': 'Computer', 'name_urdu': 'کمپیوٹر'},
]


class Command(BaseCommand):
    help = 'Seed reference skills for profiles (idempotent).'

    def handle(self, *args, **options):
        created_count = 0
        for skill_data in SKILLS:
            _, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults={'name_urdu': skill_data.get('name_urdu', '')},
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created skill: {skill_data["name"]}')
        self.stdout.write(
            self.style.SUCCESS(f'Seed complete: {created_count} skill(s) created.')
        )
