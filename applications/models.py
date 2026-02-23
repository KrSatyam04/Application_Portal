import os
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


SAFE_FILENAME_PATTERN = re.compile(r'[^A-Za-z0-9\-_. ]+')
WHITESPACE_PATTERN = re.compile(r'\s+')


def sanitize_filename(value: str) -> str:
    cleaned = SAFE_FILENAME_PATTERN.sub('', value)
    cleaned = WHITESPACE_PATTERN.sub(' ', cleaned).strip()
    return cleaned


def document_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lstrip('.')
    requirement = instance.requirement
    profile = instance.profile
    base_name = f"{profile.first_name} {profile.last_name} {requirement.display_name}"
    base_name = sanitize_filename(base_name)
    existing_count = DocumentUpload.objects.filter(profile=profile, requirement=requirement).count()
    suffix = f" ({existing_count + 1})" if existing_count >= 1 else ''
    final_name = f"{base_name}{suffix}.{ext}" if ext else f"{base_name}{suffix}"
    final_name = sanitize_filename(final_name)
    return f"uploads/{profile.id}/{final_name}"


class CourseTemplate(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CourseDetailField(models.Model):
    course = models.ForeignKey(CourseTemplate, related_name='detail_fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=120)
    key = models.CharField(max_length=80)
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.name} - {self.label}"


class CourseDocumentRequirement(models.Model):
    course = models.ForeignKey(CourseTemplate, related_name='document_requirements', on_delete=models.CASCADE)
    key = models.CharField(max_length=80)
    display_name = models.CharField(max_length=120)
    allowed_file_types = models.CharField(max_length=255, help_text='Comma-separated file extensions')
    mandatory = models.BooleanField(default=True)
    max_file_size_mb = models.PositiveIntegerField(default=10)
    allow_multiple = models.BooleanField(default=False)

    def allowed_extensions(self):
        return [ext.strip().lower() for ext in self.allowed_file_types.split(',') if ext.strip()]

    def __str__(self):
        return f"{self.course.name} - {self.display_name}"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    application_id = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=30)
    course = models.ForeignKey(CourseTemplate, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.application_id})"


class StudentDetailValue(models.Model):
    profile = models.ForeignKey(StudentProfile, related_name='detail_values', on_delete=models.CASCADE)
    field = models.ForeignKey(CourseDetailField, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'field')


class DocumentUpload(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]

    profile = models.ForeignKey(StudentProfile, related_name='uploads', on_delete=models.CASCADE)
    requirement = models.ForeignKey(CourseDocumentRequirement, on_delete=models.CASCADE)
    file = models.FileField(upload_to=document_upload_path)
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploads')

    def save(self, *args, **kwargs):
        if not self.pk:
            existing = DocumentUpload.objects.filter(profile=self.profile, requirement=self.requirement)
            self.version = existing.count() + 1
            if not self.requirement.allow_multiple:
                existing.update(is_active=False)
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        if self.file:
            self.stored_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.profile} - {self.requirement.display_name} v{self.version}"


class DocumentReviewAction(models.Model):
    upload = models.ForeignKey(DocumentUpload, related_name='review_actions', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=DocumentUpload.STATUS_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=120)
    target = models.CharField(max_length=120)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} - {self.target}"
