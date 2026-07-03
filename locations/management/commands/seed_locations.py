from django.core.management.base import BaseCommand

from locations.models import City, District, Province


PROVINCES = [
    {'name': 'Punjab', 'name_urdu': 'پنجاب'},
    {'name': 'Sindh', 'name_urdu': 'سندھ'},
    {'name': 'Khyber Pakhtunkhwa', 'name_urdu': 'خیبر پختونخوا'},
    {'name': 'Balochistan', 'name_urdu': 'بلوچستان'},
    {'name': 'Gilgit-Baltistan', 'name_urdu': 'گلگت بلتستان'},
    {'name': 'Azad Jammu & Kashmir', 'name_urdu': 'آزاد جموں و کشمیر'},
    {'name': 'Islamabad Capital Territory', 'name_urdu': 'اسلام آباد کی وفاقی دارالحکومت'},
]

CITIES_BY_PROVINCE = {
    'Punjab': [
        ('Lahore', 'لاہور'),
        ('Faisalabad', 'فیصل آباد'),
        ('Rawalpindi', 'راولپنڈی'),
        ('Multan', 'ملتان'),
        ('Gujranwala', 'گوجرانوالہ'),
        ('Sialkot', 'سیالکوٹ'),
        ('Bahawalpur', 'بہاولپور'),
        ('Sargodha', 'سرگودھا'),
        ('Sheikhupura', 'شیخوپورہ'),
        ('Jhang', 'جھنگ'),
        ('Gujrat', 'گجرات'),
        ('Sahiwal', 'ساہیوال'),
        ('Okara', 'اوکاڑہ'),
        ('Kasur', 'قصور'),
        ('Dera Ghazi Khan', 'ڈیرہ غازی خان'),
        ('Muzaffargarh', 'مظفر گڑھ'),
        ('Rahim Yar Khan', 'رحیم یار خان'),
        ('Chiniot', 'چنیوٹ'),
        ('Kamoke', 'کامونکے'),
        ('Hafizabad', 'حافظ آباد'),
    ],
    'Sindh': [
        ('Karachi', 'کراچی'),
        ('Hyderabad', 'حیدرآباد'),
        ('Sukkur', 'سکھر'),
        ('Larkana', 'لاڑکانہ'),
        ('Nawabshah', 'نواب شاہ'),
        ('Mirpur Khas', 'میرپور خاص'),
        ('Jacobabad', 'جیکب آباد'),
        ('Shikarpur', 'شکارپور'),
        ('Khairpur', 'خیرپور'),
        ('Dadu', 'دادو'),
        ('Badin', 'بدین'),
        ('Thatta', 'ٹھٹہ'),
        ('Sanghar', 'سنگھڑ'),
        ('Umerkot', 'عمرکوٹ'),
        ('Ghotki', 'گھوٹکی'),
        ('Kotri', 'کوٹری'),
        ('Matiari', 'مٹیاری'),
        ('Mirpur Sakro', 'میرپور ساکرو'),
    ],
    'Khyber Pakhtunkhwa': [
        ('Peshawar', 'پشاور'),
        ('Mardan', 'مردان'),
        ('Mingora', 'مینگورہ'),
        ('Kohat', 'کوہاٹ'),
        ('Abbottabad', 'ایبٹ آباد'),
        ('Dera Ismail Khan', 'ڈیرہ اسماعیل خان'),
        ('Mansehra', 'مانسہرہ'),
        ('Bannu', 'بنوں'),
        ('Swabi', 'صوابی'),
        ('Charsadda', 'چارسدہ'),
        ('Nowshera', 'نوشہرہ'),
        ('Haripur', 'ہری پور'),
        ('Timergara', 'تیمرگرہ'),
        ('Parachinar', 'پاراچنار'),
        ('Tank', 'ٹانک'),
        ('Batkhela', 'بٹ خیلہ'),
        ('Chitral', 'چترال'),
        ('Hangu', 'ہنگو'),
    ],
    'Balochistan': [
        ('Quetta', 'کوئٹہ'),
        ('Turbat', 'تربت'),
        ('Khuzdar', 'خضدار'),
        ('Chaman', 'چمن'),
        ('Hub', 'حب'),
        ('Sibi', 'سبی'),
        ('Zhob', 'ژوب'),
        ('Gwadar', 'گوادر'),
        ('Dera Murad Jamali', 'ڈیرہ مراد جمالی'),
        ('Loralai', 'لورالائی'),
        ('Pasni', 'پسنی'),
        ('Mastung', 'مستونگ'),
        ('Nushki', 'نوشکی'),
        ('Kalat', 'کلات'),
        ('Usta Muhammad', 'اوستہ محمد'),
    ],
    'Gilgit-Baltistan': [
        ('Gilgit', 'گلگت'),
        ('Skardu', 'سکردو'),
        ('Chilas', 'چلاس'),
        ('Hunza', 'ہنزہ'),
        ('Ghizer', 'غذر'),
        ('Astore', 'استور'),
        ('Diamer', 'دیامر'),
        ('Ghanche', 'گھانچے'),
        ('Kharmang', 'کھرمنگ'),
        ('Shigar', 'شگر'),
        ('Nagar', 'نگر'),
        ('Gupis', 'گوپس'),
    ],
    'Azad Jammu & Kashmir': [
        ('Muzaffarabad', 'مظفرآباد'),
        ('Mirpur', 'میرپور'),
        ('Kotli', 'کوٹلی'),
        ('Rawalakot', 'راولاکوٹ'),
        ('Bagh', 'باغ'),
        ('Bhimber', 'بھمبر'),
        ('Pallandri', 'پلندری'),
        ('Hattian Bala', 'ہٹیاں بالا'),
        ('Neelum', 'نیلم'),
        ('Haveli', 'حویلی'),
        ('Sudhanoti', 'سدھنوتی'),
        ('Barnala', 'برنالہ'),
    ],
    'Islamabad Capital Territory': [
        ('Islamabad', 'اسلام آباد'),
    ],
}

# Sample districts for major cities (placeholder data for structure testing)
SAMPLE_DISTRICTS = {
    'Lahore': [
        ('Lahore City', 'لاہور سٹی'),
        ('Lahore Cantonment', 'لاہور کینٹ'),
        ('Model Town', 'ماڈل ٹاؤن'),
    ],
    'Karachi': [
        ('Karachi East', 'کراچی مشرقی'),
        ('Karachi West', 'کراچی مغربی'),
        ('Karachi South', 'کراچی جنوبی'),
    ],
    'Peshawar': [
        ('Peshawar City', 'پشاور سٹی'),
        ('University Town', 'یونیورسٹی ٹاؤن'),
        ('Hayatabad', 'حیات آباد'),
    ],
}


class Command(BaseCommand):
    help = 'Seed Pakistan provinces, major cities, and sample districts (idempotent).'

    def handle(self, *args, **options):
        provinces_created = 0
        cities_created = 0
        districts_created = 0

        for province_data in PROVINCES:
            province, created = Province.objects.get_or_create(
                name=province_data['name'],
                defaults={'name_urdu': province_data['name_urdu']},
            )
            if created:
                provinces_created += 1
                self.stdout.write(f'  Created province: {province.name}')
            else:
                if province.name_urdu != province_data['name_urdu']:
                    province.name_urdu = province_data['name_urdu']
                    province.save(update_fields=['name_urdu'])

            for city_name, city_urdu in CITIES_BY_PROVINCE.get(province.name, []):
                city, created = City.objects.get_or_create(
                    name=city_name,
                    province=province,
                    defaults={'name_urdu': city_urdu},
                )
                if created:
                    cities_created += 1
                else:
                    if city.name_urdu != city_urdu:
                        city.name_urdu = city_urdu
                        city.save(update_fields=['name_urdu'])

                for district_name, district_urdu in SAMPLE_DISTRICTS.get(city_name, []):
                    district, created = District.objects.get_or_create(
                        name=district_name,
                        city=city,
                        defaults={'name_urdu': district_urdu},
                    )
                    if created:
                        districts_created += 1
                    else:
                        if district.name_urdu != district_urdu:
                            district.name_urdu = district_urdu
                            district.save(update_fields=['name_urdu'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {provinces_created} provinces, '
                f'{cities_created} cities, {districts_created} districts created.'
            )
        )
