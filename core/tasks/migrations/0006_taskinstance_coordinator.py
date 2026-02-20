from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_taskinstance_end_date_taskinstance_start_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='taskinstance',
            name='coordinator',
            field=models.ForeignKey(
                blank=True,
                help_text='Coordinator responsible for overseeing this task.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='coordinated_tasks',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
