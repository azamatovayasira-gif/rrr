from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_profile_map_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='map_number',
        ),
    ]
