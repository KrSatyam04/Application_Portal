import os
import shutil
import tempfile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CourseTemplate, CourseDocumentRequirement, StudentProfile, DocumentUpload

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ApplicationPortalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.course = CourseTemplate.objects.create(name='Medicine', code='MED')
        cls.requirement = CourseDocumentRequirement.objects.create(
            course=cls.course,
            key='passport',
            display_name='Passport',
            allowed_file_types='pdf',
            mandatory=True,
            max_file_size_mb=1,
            allow_multiple=False,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if os.path.exists(TEMP_MEDIA_ROOT):
            shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            password='password',
            first_name='Kumar',
            last_name='Satyam',
            email='student@example.com',
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            phone='12345',
            application_id='APP001',
            course=self.course,
        )
        self.other_user = User.objects.create_user(
            username='student2',
            password='password',
            first_name='Other',
            last_name='Student',
            email='other@example.com',
        )
        StudentProfile.objects.create(
            user=self.other_user,
            phone='67890',
            application_id='APP002',
            course=self.course,
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            is_staff=True,
        )

    def test_upload_and_renaming(self):
        self.client.login(username='student1', password='password')
        file_data = SimpleUploadedFile('passport.pdf', b'filecontent', content_type='application/pdf')
        response = self.client.post(
            reverse('upload_document', args=[self.requirement.id]),
            {'file': file_data},
        )
        self.assertEqual(response.status_code, 302)
        upload = DocumentUpload.objects.get(profile=self.student_profile)
        self.assertTrue(upload.stored_filename.startswith('Kumar Satyam Passport'))
        self.assertTrue(upload.stored_filename.endswith('.pdf'))

    def test_upload_validation_rejects_wrong_type(self):
        self.client.login(username='student1', password='password')
        file_data = SimpleUploadedFile('passport.txt', b'filecontent', content_type='text/plain')
        response = self.client.post(
            reverse('upload_document', args=[self.requirement.id]),
            {'file': file_data},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid file type')

    def test_student_cannot_access_other_documents(self):
        self.client.login(username='student1', password='password')
        file_data = SimpleUploadedFile('passport.pdf', b'filecontent', content_type='application/pdf')
        self.client.post(
            reverse('upload_document', args=[self.requirement.id]),
            {'file': file_data},
        )
        upload = DocumentUpload.objects.get(profile=self.student_profile)
        self.client.logout()
        self.client.login(username='student2', password='password')
        response = self.client.get(reverse('student_download_document', args=[upload.id]))
        self.assertEqual(response.status_code, 404)

    def test_admin_can_download_document(self):
        self.client.login(username='student1', password='password')
        file_data = SimpleUploadedFile('passport.pdf', b'filecontent', content_type='application/pdf')
        self.client.post(
            reverse('upload_document', args=[self.requirement.id]),
            {'file': file_data},
        )
        upload = DocumentUpload.objects.get(profile=self.student_profile)
        self.client.logout()
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('student_download_document', args=[upload.id]))
        self.assertEqual(response.status_code, 200)
