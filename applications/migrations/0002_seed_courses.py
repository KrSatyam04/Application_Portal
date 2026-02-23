from django.db import migrations


def seed_courses(apps, schema_editor):
    CourseTemplate = apps.get_model('applications', 'CourseTemplate')
    CourseDetailField = apps.get_model('applications', 'CourseDetailField')
    CourseDocumentRequirement = apps.get_model('applications', 'CourseDocumentRequirement')

    courses = [
        {
            'name': 'Medicine',
            'code': 'MED',
            'details': [
                ('passport_number', 'Passport Number', True),
                ('dob', 'Date of Birth', True),
                ('intake', 'Intake Term', True),
                ('preferred_university', 'Preferred University', False),
            ],
            'documents': [
                ('passport', 'Passport', 'pdf,jpg,png', True, 5, False),
                ('transcripts', 'Academic Transcripts', 'pdf', True, 10, True),
                ('recommendation', 'Recommendation Letter', 'pdf', True, 5, False),
                ('english_test', 'English Test Score', 'pdf', False, 5, False),
            ],
        },
        {
            'name': 'Engineering',
            'code': 'ENG',
            'details': [
                ('passport_number', 'Passport Number', True),
                ('dob', 'Date of Birth', True),
                ('intake', 'Intake Term', True),
                ('specialization', 'Preferred Specialization', False),
            ],
            'documents': [
                ('passport', 'Passport', 'pdf,jpg,png', True, 5, False),
                ('transcripts', 'Academic Transcripts', 'pdf', True, 10, True),
                ('resume', 'Resume/CV', 'pdf,doc,docx', True, 5, False),
                ('portfolio', 'Project Portfolio', 'pdf', False, 10, True),
            ],
        },
        {
            'name': 'Master Program',
            'code': 'MSTR',
            'details': [
                ('passport_number', 'Passport Number', True),
                ('dob', 'Date of Birth', True),
                ('intake', 'Intake Term', True),
                ('research_interest', 'Research Interest', True),
            ],
            'documents': [
                ('passport', 'Passport', 'pdf,jpg,png', True, 5, False),
                ('bachelor_transcript', 'Bachelor Transcript', 'pdf', True, 10, True),
                ('statement', 'Statement of Purpose', 'pdf', True, 5, False),
                ('recommendation', 'Recommendation Letter', 'pdf', False, 5, True),
            ],
        },
    ]

    for course_data in courses:
        course, _ = CourseTemplate.objects.get_or_create(
            code=course_data['code'],
            defaults={'name': course_data['name']},
        )
        if course.name != course_data['name']:
            course.name = course_data['name']
            course.save()
        for key, label, required in course_data['details']:
            CourseDetailField.objects.update_or_create(
                course=course,
                key=key,
                defaults={'label': label, 'required': required},
            )
        for key, display, types, mandatory, size, multiple in course_data['documents']:
            CourseDocumentRequirement.objects.update_or_create(
                course=course,
                key=key,
                defaults={
                    'display_name': display,
                    'allowed_file_types': types,
                    'mandatory': mandatory,
                    'max_file_size_mb': size,
                    'allow_multiple': multiple,
                },
            )


def unseed_courses(apps, schema_editor):
    CourseTemplate = apps.get_model('applications', 'CourseTemplate')
    CourseTemplate.objects.filter(code__in=['MED', 'ENG', 'MSTR']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_courses, unseed_courses),
    ]
