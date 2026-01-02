from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from applications import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/details/', views.student_details, name='student_details'),
    path('student/upload/<int:requirement_id>/', views.upload_document, name='upload_document'),
    path('student/uploads/<int:upload_id>/download/', views.student_download_document, name='student_download_document'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/student/<int:profile_id>/', views.admin_student_detail, name='admin_student_detail'),
    path('admin-dashboard/student/<int:profile_id>/zip/', views.admin_download_zip, name='admin_download_zip'),
    path('admin-dashboard/export/csv/', views.admin_export_csv, name='admin_export_csv'),
    path('admin-dashboard/upload/<int:upload_id>/review/', views.admin_review_upload, name='admin_review_upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
