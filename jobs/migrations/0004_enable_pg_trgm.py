from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_alter_jobposting_status'),
    ]

    operations = [
        TrigramExtension(),
    ]
