import csv
import io
import os
import zipfile
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DetailValueForm, DocumentUploadForm, ReviewForm, StudentProfileForm, StudentSignupForm
from .models import (
    AuditLog,
    CourseDocumentRequirement,
    CourseTemplate,
    DocumentReviewAction,
    DocumentUpload,
    StudentDetailValue,
    StudentProfile,
)


def home(request):
    return render(request, 'applications/home.html')


def signup(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('student_profile')
    else:
        form = StudentSignupForm()
    return render(request, 'applications/signup.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('student_dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'applications/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


def get_student_profile(user: User) -> StudentProfile:
    return get_object_or_404(StudentProfile, user=user)


def latest_upload_for(profile, requirement):
    return (
        DocumentUpload.objects.filter(profile=profile, requirement=requirement, is_active=True)
        .order_by('-uploaded_at')
        .first()
    )


def get_requirement_status(profile, requirement):
    upload = latest_upload_for(profile, requirement)
    if not upload:
        return 'pending', None
    return upload.status, upload


def compute_completion(profile):
    if not profile.course:
        return 0
    requirements = profile.course.document_requirements.all()
    mandatory = [req for req in requirements if req.mandatory]
    if not mandatory:
        return 0
    approved = 0
    for req in mandatory:
        status, _ = get_requirement_status(profile, req)
        if status == 'approved':
            approved += 1
    return int((approved / len(mandatory)) * 100)


@login_required
def student_profile(request):
    profile = get_student_profile(request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('student_details')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'applications/student_profile.html', {'form': form})


@login_required
def student_details(request):
    profile = get_student_profile(request.user)
    if not profile.course:
        return redirect('student_profile')
    detail_fields = profile.course.detail_fields.all()
    existing_values = {dv.field.key: dv.value for dv in profile.detail_values.select_related('field')}
    if request.method == 'POST':
        form = DetailValueForm(request.POST, detail_fields=detail_fields, initial_values=existing_values)
        if form.is_valid():
            for field in detail_fields:
                value = form.cleaned_data.get(field.key, '')
                StudentDetailValue.objects.update_or_create(
                    profile=profile,
                    field=field,
                    defaults={'value': value},
                )
            messages.success(request, 'Details saved.')
            return redirect('student_dashboard')
    else:
        form = DetailValueForm(detail_fields=detail_fields, initial_values=existing_values)
    return render(request, 'applications/student_details.html', {'form': form, 'course': profile.course})


@login_required
def student_dashboard(request):
    profile = get_student_profile(request.user)
    if not profile.course:
        return redirect('student_profile')
    requirements = profile.course.document_requirements.all()
    checklist = []
    pending_items = []
    for req in requirements:
        status, upload = get_requirement_status(profile, req)
        last_updated = upload.uploaded_at if upload else None
        latest_note = None
        if upload:
            action = upload.review_actions.order_by('-created_at').first()
            latest_note = action.note if action else ''
        if req.mandatory and status != 'approved':
            pending_items.append(req.display_name)
        checklist.append({
            'requirement': req,
            'status': status,
            'upload': upload,
            'last_updated': last_updated,
            'note': latest_note,
        })
    completion = compute_completion(profile)
    return render(
        request,
        'applications/student_dashboard.html',
        {
            'profile': profile,
            'checklist': checklist,
            'completion': completion,
            'pending_items': pending_items,
        },
    )


@login_required
def upload_document(request, requirement_id):
    profile = get_student_profile(request.user)
    requirement = get_object_or_404(CourseDocumentRequirement, id=requirement_id, course=profile.course)
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            ext = os.path.splitext(uploaded_file.name)[1].lstrip('.').lower()
            allowed = requirement.allowed_extensions()
            if allowed and ext not in allowed:
                form.add_error('file', f"Invalid file type. Allowed: {', '.join(allowed)}")
            max_size_bytes = requirement.max_file_size_mb * 1024 * 1024
            if uploaded_file.size > max_size_bytes:
                form.add_error('file', f"File too large. Max size: {requirement.max_file_size_mb} MB")
            if not form.errors:
                upload = form.save(commit=False)
                upload.profile = profile
                upload.requirement = requirement
                upload.uploaded_by = request.user
                upload.original_filename = uploaded_file.name
                upload.save()
                AuditLog.objects.create(
                    actor=request.user,
                    action='upload',
                    target=f"{profile.application_id}:{requirement.key}",
                )
                messages.success(request, 'Document uploaded.')
                return redirect('student_dashboard')
    else:
        form = DocumentUploadForm()
    return render(
        request,
        'applications/upload_document.html',
        {'form': form, 'requirement': requirement, 'profile': profile},
    )


@login_required
def student_download_document(request, upload_id):
    if request.user.is_staff:
        upload = get_object_or_404(DocumentUpload, id=upload_id)
    else:
        profile = get_student_profile(request.user)
        upload = get_object_or_404(DocumentUpload, id=upload_id, profile=profile)
    if not upload.file:
        raise Http404()
    return FileResponse(upload.file.open('rb'), as_attachment=True, filename=upload.stored_filename)


def staff_required(view_func):
    return user_passes_test(lambda user: user.is_staff)(view_func)


@staff_required
def admin_dashboard(request):
    profiles = StudentProfile.objects.select_related('user', 'course')
    course_filter = request.GET.get('course')
    status_filter = request.GET.get('status')
    query = request.GET.get('q')
    if course_filter:
        profiles = profiles.filter(course__code=course_filter)
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(application_id__icontains=query)
        )
    dashboard_rows = []
    for profile in profiles:
        completion = compute_completion(profile)
        needs_revision = DocumentUpload.objects.filter(profile=profile, status='needs_revision').exists()
        last_upload = profile.uploads.order_by('-uploaded_at').first()
        status_label = 'Complete' if completion == 100 else 'Needs Revision' if needs_revision else 'In Progress'
        if status_filter and status_filter != status_label:
            continue
        dashboard_rows.append({
            'profile': profile,
            'completion': completion,
            'last_activity': last_upload.uploaded_at if last_upload else None,
            'status_label': status_label,
            'needs_revision': needs_revision,
        })
    totals = StudentProfile.objects.count()
    total_complete = sum(1 for row in dashboard_rows if row['status_label'] == 'Complete')
    total_needs_revision = sum(1 for row in dashboard_rows if row['status_label'] == 'Needs Revision')
    total_in_progress = totals - total_complete - total_needs_revision
    courses = CourseTemplate.objects.all()
    return render(
        request,
        'applications/admin_dashboard.html',
        {
            'rows': dashboard_rows,
            'totals': totals,
            'total_complete': total_complete,
            'total_needs_revision': total_needs_revision,
            'total_in_progress': total_in_progress,
            'courses': courses,
        },
    )


@staff_required
def admin_student_detail(request, profile_id):
    profile = get_object_or_404(StudentProfile, id=profile_id)
    requirements = profile.course.document_requirements.all() if profile.course else []
    checklist = []
    for req in requirements:
        status, upload = get_requirement_status(profile, req)
        checklist.append({
            'requirement': req,
            'status': status,
            'upload': upload,
            'review_form': ReviewForm(initial={'status': upload.status if upload else 'uploaded'}),
        })
    detail_values = profile.detail_values.select_related('field').order_by('field__label')
    return render(
        request,
        'applications/admin_student_detail.html',
        {
            'profile': profile,
            'checklist': checklist,
            'detail_values': detail_values,
        },
    )


@staff_required
def admin_review_upload(request, upload_id):
    upload = get_object_or_404(DocumentUpload, id=upload_id)
    if request.method != 'POST':
        return redirect('admin_student_detail', profile_id=upload.profile.id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        status = form.cleaned_data['status']
        note = form.cleaned_data['note']
        upload.status = status
        upload.save()
        DocumentReviewAction.objects.create(
            upload=upload,
            reviewer=request.user,
            status=status,
            note=note,
        )
        AuditLog.objects.create(
            actor=request.user,
            action='review',
            target=f"{upload.profile.application_id}:{upload.requirement.key}",
            note=note,
        )
        messages.success(request, 'Review saved.')
    return redirect('admin_student_detail', profile_id=upload.profile.id)


@staff_required
def admin_download_zip(request, profile_id):
    profile = get_object_or_404(StudentProfile, id=profile_id)
    if not profile.course:
        raise Http404()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for requirement in profile.course.document_requirements.all():
            uploads = DocumentUpload.objects.filter(profile=profile, requirement=requirement, is_active=True)
            if requirement.allow_multiple:
                selected = uploads
            else:
                selected = uploads.order_by('-uploaded_at')[:1]
            for upload in selected:
                if upload.file:
                    with upload.file.open('rb') as file_handle:
                        archive.writestr(upload.stored_filename, file_handle.read())
    buffer.seek(0)
    filename = f"{profile.application_id}_documents.zip"
    AuditLog.objects.create(
        actor=request.user,
        action='download_zip',
        target=profile.application_id,
    )
    return FileResponse(buffer, as_attachment=True, filename=filename)


@staff_required
def admin_export_csv(request):
    profiles = StudentProfile.objects.select_related('user', 'course')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="document_status_report.csv"'
    writer = csv.writer(response)
    all_requirements = list(CourseDocumentRequirement.objects.select_related('course').order_by('course__name', 'display_name'))
    header = ['Application ID', 'Name', 'Email', 'Course', 'Completion %']
    header.extend([f"{req.course.code}:{req.display_name}" for req in all_requirements])
    writer.writerow(header)
    for profile in profiles:
        completion = compute_completion(profile)
        row = [
            profile.application_id,
            profile.user.get_full_name(),
            profile.user.email,
            profile.course.name if profile.course else '',
            completion,
        ]
        status_map = {}
        if profile.course:
            for requirement in profile.course.document_requirements.all():
                status, _ = get_requirement_status(profile, requirement)
                status_map[requirement.id] = status
        for requirement in all_requirements:
            row.append(status_map.get(requirement.id, ''))
        writer.writerow(row)
    AuditLog.objects.create(
        actor=request.user,
        action='export_csv',
        target='document_status_report',
    )
    return response
