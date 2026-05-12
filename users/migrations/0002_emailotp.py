import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp', models.CharField(max_length=4)),
                ('expires_at', models.DateTimeField()),
                ('last_sent_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_verified', models.BooleanField(default=False)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='email_otp',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
