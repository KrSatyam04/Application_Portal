from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import StudentProfile, CourseTemplate, StudentDetailValue, DocumentUpload


class StudentSignupForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=30)
    application_id = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'application_id', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                application_id=self.cleaned_data['application_id'],
            )
        return user


class StudentProfileForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=CourseTemplate.objects.all(), required=True)

    class Meta:
        model = StudentProfile
        fields = ('phone', 'application_id', 'course')


class DetailValueForm(forms.Form):
    def __init__(self, *args, **kwargs):
        detail_fields = kwargs.pop('detail_fields')
        initial_values = kwargs.pop('initial_values')
        super().__init__(*args, **kwargs)
        for field in detail_fields:
            self.fields[field.key] = forms.CharField(
                label=field.label,
                required=field.required,
                initial=initial_values.get(field.key, ''),
            )


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentUpload
        fields = ('file',)


class ReviewForm(forms.Form):
    status = forms.ChoiceField(choices=DocumentUpload.STATUS_CHOICES)
    note = forms.CharField(widget=forms.Textarea, required=False)
