from django.contrib import admin
from .models import (
    CourseDetailField,
    CourseDocumentRequirement,
    CourseTemplate,
    StudentProfile,
    StudentDetailValue,
    DocumentUpload,
    DocumentReviewAction,
    AuditLog,
)

admin.site.register(CourseTemplate)
admin.site.register(CourseDetailField)
admin.site.register(CourseDocumentRequirement)
admin.site.register(StudentProfile)
admin.site.register(StudentDetailValue)
admin.site.register(DocumentUpload)
admin.site.register(DocumentReviewAction)
admin.site.register(AuditLog)
