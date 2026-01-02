# Generated manually for initial schema.
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import applications.models
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('code', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseDetailField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=120)),
                ('key', models.CharField(max_length=80)),
                ('required', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detail_fields', to='applications.coursetemplate')),
            ],
        ),
        migrations.CreateModel(
            name='CourseDocumentRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=80)),
                ('display_name', models.CharField(max_length=120)),
                ('allowed_file_types', models.CharField(help_text='Comma-separated file extensions', max_length=255)),
                ('mandatory', models.BooleanField(default=True)),
                ('max_file_size_mb', models.PositiveIntegerField(default=10)),
                ('allow_multiple', models.BooleanField(default=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='document_requirements', to='applications.coursetemplate')),
            ],
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_id', models.CharField(max_length=50, unique=True)),
                ('phone', models.CharField(max_length=30)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='applications.coursetemplate')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StudentDetailValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='applications.coursedetailfield')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detail_values', to='applications.studentprofile')),
            ],
            options={'unique_together': {('profile', 'field')}},
        ),
        migrations.CreateModel(
            name='DocumentUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=applications.models.document_upload_path)),
                ('original_filename', models.CharField(max_length=255)),
                ('stored_filename', models.CharField(max_length=255)),
                ('version', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('uploaded', 'Uploaded'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('needs_revision', 'Needs Revision')], default='uploaded', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to='applications.studentprofile')),
                ('requirement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='applications.coursedocumentrequirement')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploads', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentReviewAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('uploaded', 'Uploaded'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('needs_revision', 'Needs Revision')], max_length=20)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('upload', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_actions', to='applications.documentupload')),
            ],
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=120)),
                ('target', models.CharField(max_length=120)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
