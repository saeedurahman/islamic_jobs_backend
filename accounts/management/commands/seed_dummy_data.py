from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from accounts.utils import generate_username, normalize_phone_number
from applications.models import Application
from employers.models import Employer
from jobs.models import JobPosting
from locations.models import City, District
from profiles.models import (
    AsriEducation,
    DarseNizami,
    HifzEducation,
    Ijazah,
    Language,
    Profile,
    Skill,
)

DEMO_EMAIL_DOMAIN = '@deenijobs.test'
DEMO_PASSWORD = 'Demo1234!'


def clear_demo_data():
    deleted_users, _ = User.objects.filter(email__endswith=DEMO_EMAIL_DOMAIN).delete()
    return deleted_users


def get_city(city_name, province_name=None):
    qs = City.objects.select_related('province').filter(name=city_name)
    if province_name:
        qs = qs.filter(province__name=province_name)
    city = qs.first()
    if not city:
        raise ValueError(f'City not found: {city_name}' + (f' ({province_name})' if province_name else ''))
    return city


def get_first_district(city):
    return District.objects.filter(city=city).first()


def get_language(name):
    lang = Language.objects.filter(name=name).first()
    if not lang:
        raise ValueError(f'Language not found: {name}. Run: python manage.py seed_languages')
    return lang


def get_skill(name):
    skill = Skill.objects.filter(name=name).first()
    if not skill:
        raise ValueError(f'Skill not found: {name}. Run: python manage.py seed_skills')
    return skill


def create_demo_user(email, phone, role, first_name, last_name):
    phone = normalize_phone_number(phone)
    user = User(
        username=generate_username(email),
        email=email,
        phone_number=phone,
        user_role=role,
        first_name=first_name,
        last_name=last_name,
    )
    user.set_password(DEMO_PASSWORD)
    user.save()
    return user


def age_to_dob(age):
    today = date.today()
    return date(today.year - age, 6, 15)


SEEKER_DATA = [
    {
        'email': 'demo.seeker1@deenijobs.test',
        'phone': '03001000001',
        'first_name': 'Ahmed',
        'last_name': 'Khan',
        'full_name': 'Maulana Ahmed Ali Khan',
        'father_name': 'Muhammad Aslam Khan',
        'age': 32,
        'marital_status': Profile.MaritalStatus.MARRIED,
        'city_name': 'Lahore',
        'province_name': 'Punjab',
        'user_category': Profile.UserCategory.IMAM,
        'is_public': True,
        'verified': True,
        'languages': ['Urdu', 'Arabic', 'Punjabi'],
        'skills': ['Teaching', 'Public Speaking'],
        'islamic': [
            ('hifz', {'madrasa_name': 'Jamia Ashrafia Lahore', 'completion_year': 2008, 'teacher_name': 'Maulana Yusuf'}),
            ('dars', {'madrasa_name': 'Darul Uloom Karachi', 'wifaq_name': 'Wifaq-ul-Madaris', 'sanad_year': 2014}),
        ],
        'asri': {'level': AsriEducation.Level.BA, 'institution': 'University of Punjab', 'year': 2016},
    },
    {
        'email': 'demo.seeker2@deenijobs.test',
        'phone': '03001000002',
        'first_name': 'Hassan',
        'last_name': 'Raza',
        'full_name': 'Muhammad Hassan Raza',
        'father_name': 'Abdul Razaq',
        'age': 28,
        'marital_status': Profile.MaritalStatus.SINGLE,
        'city_name': 'Karachi',
        'province_name': 'Sindh',
        'user_category': Profile.UserCategory.MUAZZIN,
        'is_public': True,
        'verified': True,
        'languages': ['Urdu', 'Sindhi', 'Arabic'],
        'skills': ['Public Speaking', 'MS Office'],
        'islamic': [
            ('hifz', {'madrasa_name': 'Madrasa Anwar-ul-Quran Karachi', 'completion_year': 2012, 'teacher_name': 'Qari Saeed'}),
            ('ijazah', {'subject': 'Tajweed', 'ustad_name': 'Qari Abdul Basit', 'year': 2015}),
        ],
        'asri': {'level': AsriEducation.Level.MATRIC, 'institution': 'Sindh Board', 'year': 2010},
    },
    {
        'email': 'demo.seeker3@deenijobs.test',
        'phone': '03001000003',
        'first_name': 'Rahman',
        'last_name': 'Siddiqui',
        'full_name': 'Maulana Abdul Rahman Siddiqui',
        'father_name': 'Ghulam Siddiqui',
        'age': 45,
        'marital_status': Profile.MaritalStatus.MARRIED,
        'city_name': 'Islamabad',
        'province_name': 'Islamabad Capital Territory',
        'user_category': Profile.UserCategory.MUDARRIS,
        'is_public': True,
        'verified': True,
        'languages': ['Urdu', 'English', 'Arabic'],
        'skills': ['Teaching', 'Research', 'Counselling'],
        'islamic': [
            ('dars', {'madrasa_name': 'Jamia Farooqia Islamabad', 'wifaq_name': 'Tanzeem-ul-Madaris', 'sanad_year': 2005}),
            ('ijazah', {'subject': 'Sahih Bukhari', 'ustad_name': 'Maulana Tariq Jamil', 'year': 2008}),
        ],
        'asri': {'level': AsriEducation.Level.MA, 'institution': 'IIUI', 'year': 2012},
    },
    {
        'email': 'demo.seeker4@deenijobs.test',
        'phone': '03001000004',
        'first_name': 'Bilal',
        'last_name': 'Ahmad',
        'full_name': 'Qari Bilal Ahmad',
        'father_name': 'Nazir Ahmad',
        'age': 26,
        'marital_status': Profile.MaritalStatus.SINGLE,
        'city_name': 'Peshawar',
        'province_name': 'Khyber Pakhtunkhwa',
        'user_category': Profile.UserCategory.QARI,
        'is_public': False,
        'verified': False,
        'languages': ['Urdu', 'Pashto', 'Arabic'],
        'skills': ['Teaching', 'Computer'],
        'islamic': [
            ('hifz', {'madrasa_name': 'Madrasa Haqqania', 'completion_year': 2014, 'teacher_name': 'Maulana Hamid'}),
            ('ijazah', {'subject': 'Qirat Asim', 'ustad_name': 'Qari Usman', 'year': 2018}),
        ],
        'asri': {'level': AsriEducation.Level.FA, 'institution': 'Peshawar Board', 'year': 2016},
    },
    {
        'email': 'demo.seeker5@deenijobs.test',
        'phone': '03001000005',
        'first_name': 'Tariq',
        'last_name': 'Mahmood',
        'full_name': 'Maulana Tariq Mahmood',
        'father_name': 'Mahmood Hassan',
        'age': 38,
        'marital_status': Profile.MaritalStatus.MARRIED,
        'city_name': 'Faisalabad',
        'province_name': 'Punjab',
        'user_category': Profile.UserCategory.KHATEEB,
        'is_public': False,
        'verified': False,
        'languages': ['Urdu', 'Punjabi', 'English'],
        'skills': ['Public Speaking', 'Management'],
        'islamic': [
            ('dars', {'madrasa_name': 'Jamia Rehmania Faisalabad', 'wifaq_name': 'Wifaq-ul-Madaris', 'sanad_year': 2010}),
            ('hifz', {'madrasa_name': 'Local Madrasa Faisalabad', 'completion_year': 2002, 'teacher_name': 'Hafiz Kareem'}),
        ],
        'asri': {'level': AsriEducation.Level.BS, 'institution': 'GC University Faisalabad', 'year': 2014},
    },
]

EMPLOYER_DATA = [
    {
        'email': 'demo.employer1@deenijobs.test',
        'phone': '03002000001',
        'first_name': 'Khalid',
        'last_name': 'Mehmood',
        'organization_type': Employer.OrganizationType.MASJID,
        'organization_name': 'Jamia Masjid Al-Falah',
        'description': 'A well-established masjid in Lahore serving the local community for over 30 years.',
        'contact_person': 'Muhammad Khalid Mehmood',
        'city_name': 'Lahore',
        'province_name': 'Punjab',
        'contact_email': 'demo.employer1@deenijobs.test',
    },
    {
        'email': 'demo.employer2@deenijobs.test',
        'phone': '03002000002',
        'first_name': 'Farooq',
        'last_name': 'Ahmed',
        'organization_type': Employer.OrganizationType.MADRASA,
        'organization_name': 'Darul Uloom Muhammadia',
        'description': 'A renowned madrasa in Karachi offering Dars-e-Nizami and Hifz programmes.',
        'contact_person': 'Maulana Farooq Ahmed',
        'city_name': 'Karachi',
        'province_name': 'Sindh',
        'contact_email': 'demo.employer2@deenijobs.test',
    },
]


def add_islamic_education(profile, records):
    for record_type, data in records:
        if record_type == 'hifz':
            HifzEducation.objects.create(profile=profile, **data)
        elif record_type == 'dars':
            DarseNizami.objects.create(profile=profile, **data)
        elif record_type == 'ijazah':
            Ijazah.objects.create(profile=profile, **data)


class Command(BaseCommand):
    help = 'Seed demo users, profiles, employers, jobs, and applications for frontend development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all demo data (emails ending with @deenijobs.test) before seeding.',
        )

    def handle(self, *args, **options):
        if not City.objects.exists():
            self.stderr.write(self.style.ERROR(
                'No cities found. Run: python manage.py seed_locations'
            ))
            return
        if not Language.objects.exists():
            self.stderr.write(self.style.ERROR(
                'No languages found. Run: python manage.py seed_languages'
            ))
            return
        if not Skill.objects.exists():
            self.stderr.write(self.style.ERROR(
                'No skills found. Run: python manage.py seed_skills'
            ))
            return

        if options['clear']:
            deleted = clear_demo_data()
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} demo object(s).'))

        try:
            with transaction.atomic():
                seekers, employers, jobs, applications = self._seed_all()
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write(f'  Job seekers created: {len(seekers)}')
        self.stdout.write(f'  Employers created:   {len(employers)}')
        self.stdout.write(f'  Job postings:        {len(jobs)}')
        self.stdout.write(f'  Applications:        {len(applications)}')
        self.stdout.write(self.style.WARNING(
            f'\nAll demo accounts use password: {DEMO_PASSWORD}'
        ))
        self.stdout.write('Emails: demo.seeker1@deenijobs.test … demo.seeker5@deenijobs.test')
        self.stdout.write('        demo.employer1@deenijobs.test, demo.employer2@deenijobs.test')

    def _seed_all(self):
        seekers = []
        for data in SEEKER_DATA:
            seekers.append(self._create_seeker(data))

        employers = []
        for data in EMPLOYER_DATA:
            employers.append(self._create_employer(data))

        jobs = self._create_jobs(employers)
        applications = self._create_applications(seekers, jobs)
        return seekers, employers, jobs, applications

    def _create_seeker(self, data):
        user = create_demo_user(
            email=data['email'],
            phone=data['phone'],
            role=User.Role.JOB_SEEKER,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        profile = user.profile
        city = get_city(data['city_name'], data['province_name'])
        district = get_first_district(city)

        profile.full_name = data['full_name']
        profile.father_name = data['father_name']
        profile.date_of_birth = age_to_dob(data['age'])
        profile.marital_status = data['marital_status']
        profile.whatsapp_number = normalize_phone_number(data['phone'])
        profile.contact_email = data['email']
        profile.province = city.province
        profile.city = city
        profile.district = district
        profile.user_category = data['user_category']
        profile.is_public = data['is_public']
        profile.verification_status = (
            Profile.VerificationStatus.VERIFIED
            if data['verified']
            else Profile.VerificationStatus.PENDING
        )
        profile.save()

        profile.languages.set([get_language(n) for n in data['languages']])
        profile.skills.set([get_skill(n) for n in data['skills']])
        add_islamic_education(profile, data['islamic'])
        AsriEducation.objects.create(profile=profile, **data['asri'])

        profile.refresh_from_db()
        return profile

    def _create_employer(self, data):
        user = create_demo_user(
            email=data['email'],
            phone=data['phone'],
            role=User.Role.EMPLOYER,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        employer = user.employer_profile
        city = get_city(data['city_name'], data['province_name'])
        district = get_first_district(city)

        employer.organization_type = data['organization_type']
        employer.organization_name = data['organization_name']
        employer.description = data['description']
        employer.contact_person = data['contact_person']
        employer.province = city.province
        employer.city = city
        employer.district = district
        employer.whatsapp_number = normalize_phone_number(data['phone'])
        employer.contact_phone = normalize_phone_number(data['phone'])
        employer.contact_email = data['contact_email']
        employer.verification_status = Employer.VerificationStatus.VERIFIED
        employer.save()
        return employer

    def _create_jobs(self, employers):
        employer1, employer2 = employers
        lahore = get_city('Lahore', 'Punjab')
        karachi = get_city('Karachi', 'Sindh')
        islamabad = get_city('Islamabad', 'Islamabad Capital Territory')
        peshawar = get_city('Peshawar', 'Khyber Pakhtunkhwa')
        rawalpindi = get_city('Rawalpindi', 'Punjab')
        gujranwala = get_city('Gujranwala', 'Punjab')
        hyderabad = get_city('Hyderabad', 'Sindh')
        sukkur = get_city('Sukkur', 'Sindh')
        multan = get_city('Multan', 'Punjab')

        urdu = get_language('Urdu')
        arabic = get_language('Arabic')
        english = get_language('English')

        job_specs = [
            # employer1 — 5 jobs
            {
                'employer': employer1,
                'title': 'Imam Required for Daily Prayers & Jumuah',
                'description': (
                    'Jamia Masjid Al-Falah seeks a qualified Imam for five daily prayers, '
                    'Jumuah khutbah, and basic community guidance. Accommodation near the masjid is available.'
                ),
                'category': Profile.UserCategory.IMAM,
                'city': lahore,
                'salary_min': 45000,
                'salary_max': 65000,
                'accommodation_provided': True,
                'meals_provided': False,
                'experience_required': JobPosting.ExperienceRequired.THREE_TO_FIVE,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu, arabic],
            },
            {
                'employer': employer1,
                'title': 'Muazzin Needed — Fajr to Isha',
                'description': (
                    'We are looking for a muazzin with a clear, melodious voice for all five daily azans. '
                    'The candidate should be punctual and familiar with local prayer timings.'
                ),
                'category': Profile.UserCategory.MUAZZIN,
                'city': lahore,
                'salary_min': 25000,
                'salary_max': 35000,
                'accommodation_provided': False,
                'meals_provided': True,
                'experience_required': JobPosting.ExperienceRequired.ONE_TO_THREE,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu],
            },
            {
                'employer': employer1,
                'title': 'Khateeb for Weekly Jumuah Khutbah',
                'description': (
                    'Masjid committee requires an experienced khateeb for Urdu Jumuah bayan. '
                    'Topics should be relevant to community welfare and Islamic ethics.'
                ),
                'category': Profile.UserCategory.KHATEEB,
                'city': rawalpindi,
                'salary_min': 30000,
                'salary_max': 50000,
                'accommodation_provided': False,
                'meals_provided': False,
                'experience_required': JobPosting.ExperienceRequired.FIVE_PLUS,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu, english],
            },
            {
                'employer': employer1,
                'title': 'Qari for Ramadan Taraweeh',
                'description': (
                    'Seasonal position for a Qari to lead Taraweeh prayers during Ramadan. '
                    'Must have strong tajweed and ability to complete one juz per night.'
                ),
                'category': Profile.UserCategory.QARI,
                'city': lahore,
                'salary_min': 40000,
                'salary_max': 60000,
                'accommodation_provided': True,
                'meals_provided': True,
                'experience_required': JobPosting.ExperienceRequired.ONE_TO_THREE,
                'status': JobPosting.Status.ACTIVE,
                'languages': [arabic, urdu],
            },
            {
                'employer': employer1,
                'title': 'Imam Position — Position Closed',
                'description': (
                    'This Imam position has been closed. Kept for frontend status display testing.'
                ),
                'category': Profile.UserCategory.IMAM,
                'city': gujranwala,
                'salary_min': 35000,
                'salary_max': 50000,
                'accommodation_provided': False,
                'meals_provided': False,
                'experience_required': JobPosting.ExperienceRequired.THREE_TO_FIVE,
                'status': JobPosting.Status.CLOSED,
                'languages': [],
            },
            # employer2 — 5 jobs
            {
                'employer': employer2,
                'title': 'Mudarris for Dars-e-Nizami (Sania Amma)',
                'description': (
                    'Darul Uloom Muhammadia invites applications for a mudarris to teach Sania Amma subjects. '
                    'Candidates must have a sanad from a recognized wifaq.'
                ),
                'category': Profile.UserCategory.MUDARRIS,
                'city': karachi,
                'salary_min': 50000,
                'salary_max': 70000,
                'accommodation_provided': True,
                'meals_provided': True,
                'experience_required': JobPosting.ExperienceRequired.THREE_TO_FIVE,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu, arabic],
            },
            {
                'employer': employer2,
                'title': 'Quran Teacher for Children (Nazra & Tajweed)',
                'description': (
                    'Evening Quran classes for children aged 7–14. Teacher should be patient, '
                    'experienced in nazra and basic tajweed instruction.'
                ),
                'category': Profile.UserCategory.QURAN_TEACHER,
                'city': karachi,
                'salary_min': 28000,
                'salary_max': 40000,
                'accommodation_provided': False,
                'meals_provided': False,
                'experience_required': JobPosting.ExperienceRequired.ONE_TO_THREE,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu],
            },
            {
                'employer': employer2,
                'title': 'Mufti for Fatwa & Counselling',
                'description': (
                    'Part-time mufti needed for weekly fatwa sessions and family counselling. '
                    'Must hold takhassus in fiqh from a recognized institution.'
                ),
                'category': Profile.UserCategory.MUFTI,
                'city': hyderabad,
                'salary_min': 55000,
                'salary_max': 80000,
                'accommodation_provided': False,
                'meals_provided': False,
                'experience_required': JobPosting.ExperienceRequired.FIVE_PLUS,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu, arabic, english],
            },
            {
                'employer': employer2,
                'title': 'Islamic Lecturer for Weekend Bayan',
                'description': (
                    'Weekend Islamic lecture series for university students. Topics include seerah, '
                    'aqeedah, and contemporary issues facing Muslim youth.'
                ),
                'category': Profile.UserCategory.ISLAMIC_LECTURER,
                'city': sukkur,
                'salary_min': 32000,
                'salary_max': 48000,
                'accommodation_provided': False,
                'meals_provided': True,
                'experience_required': JobPosting.ExperienceRequired.THREE_TO_FIVE,
                'status': JobPosting.Status.ACTIVE,
                'languages': [urdu, english],
            },
            {
                'employer': employer2,
                'title': 'Mudarris — Arabic Grammar (Position Filled)',
                'description': (
                    'This mudarris position has been filled. Retained for frontend filled-status testing.'
                ),
                'category': Profile.UserCategory.MUDARRIS,
                'city': multan,
                'salary_min': 42000,
                'salary_max': 58000,
                'accommodation_provided': True,
                'meals_provided': False,
                'experience_required': JobPosting.ExperienceRequired.THREE_TO_FIVE,
                'status': JobPosting.Status.FILLED,
                'languages': [arabic],
            },
        ]

        jobs = []
        for spec in job_specs:
            languages = spec.pop('languages')
            city = spec.pop('city')
            job = JobPosting.objects.create(
                province=city.province,
                city=city,
                district=get_first_district(city),
                sect=JobPosting.Sect.NOT_SPECIFIED,
                **spec,
            )
            if languages:
                job.required_languages.set(languages)
            jobs.append(job)
        return jobs

    def _create_applications(self, seekers, jobs):
        # jobs[0]=imam, [1]=muazzin, [2]=khateeb, [3]=qari, [5]=mudarris
        pairs = [
            (seekers[0], jobs[0], Application.Status.APPLIED,
             'I have 8 years of experience leading prayers and delivering Jumuah khutbah in Lahore.'),
            (seekers[1], jobs[1], Application.Status.SHORTLISTED,
             'My voice has been praised by the local community. I am punctual and reliable for all five azans.'),
            (seekers[2], jobs[5], Application.Status.INTERVIEW,
             'I have taught Dars-e-Nizami for 12 years and hold ijazah in Sahih Bukhari. Available for interview anytime.'),
            (seekers[3], jobs[3], Application.Status.HIRED,
             'Completed Hifz and Qirat Asim ijazah. Led Taraweeh at three masajid in Peshawar.'),
            (seekers[4], jobs[2], Application.Status.REJECTED,
             'Experienced khateeb with strong Urdu bayan skills. I have delivered khutbah at multiple masajid.'),
        ]

        applications = []
        for profile, job, status, cover_note in pairs:
            app = Application.objects.create(
                job=job,
                applicant=profile,
                status=status,
                cover_note=cover_note,
            )
            applications.append(app)
        return applications
