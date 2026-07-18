from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import UserProfile


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_initial = forms.CharField(max_length=1, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1', 'placeholder': 'M.I.', 'style': 'text-transform: uppercase;'}))
    SUFFIX_CHOICES = (
        ('', 'None'),
        ('Jr.', 'Jr.'),
        ('Sr.', 'Sr.'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
        ('V', 'V'),
    )
    suffix = forms.ChoiceField(choices=SUFFIX_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['middle_initial'].widget.attrs['placeholder'] = 'M.I.'
        self.fields['email'].widget.attrs['placeholder'] = 'Email address'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_middle_initial(self):
        mi = self.cleaned_data.get('middle_initial', '')
        if mi:
            mi = mi.strip()[0].upper()
        return mi

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Auto-generate username from email prefix
        base_username = self.cleaned_data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username

        if commit:
            user.save()
            profile = user.profile
            profile.middle_initial = self.cleaned_data.get('middle_initial', '')
            profile.suffix = self.cleaned_data.get('suffix', '')
            profile.role = 'contributor'
            profile.status = 'pending'
            profile.save()

        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email address',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
    }))


class AdminCreateUserForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_initial = forms.CharField(max_length=1, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1', 'placeholder': 'M.I.', 'style': 'text-transform: uppercase;'}))
    suffix = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists')
        return email

    def clean_middle_initial(self):
        mi = self.cleaned_data.get('middle_initial', '')
        if mi:
            mi = mi.strip()[0].upper()
        return mi

    def save(self, commit=True):
        user = super(AdminCreateUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        base_username = self.cleaned_data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            profile = user.profile
            profile.middle_initial = self.cleaned_data.get('middle_initial', '')
            profile.suffix = self.cleaned_data.get('suffix', '')
            profile.role = self.cleaned_data['role']
            profile.status = 'approved'
            profile.save()

        return user


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_initial = forms.CharField(max_length=1, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1', 'placeholder': 'M.I.', 'style': 'text-transform: uppercase;'}))
    suffix = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['bio'].initial = self.instance.profile.bio
            self.fields['middle_initial'].initial = self.instance.profile.middle_initial
            self.fields['suffix'].initial = self.instance.profile.suffix
            self.fields['profile_picture'].initial = self.instance.profile.profile_picture

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Email already exists')
        return email

    def clean_middle_initial(self):
        mi = self.cleaned_data.get('middle_initial', '')
        if mi:
            mi = mi.strip()[0].upper()
        return mi

    def save(self, commit=True):
        user = super(UserProfileForm, self).save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'profile'):
                user.profile.bio = self.cleaned_data.get('bio')
                user.profile.middle_initial = self.cleaned_data.get('middle_initial', '')
                user.profile.suffix = self.cleaned_data.get('suffix', '')
                profile_picture = self.cleaned_data.get('profile_picture')
                if profile_picture:
                    user.profile.profile_picture = profile_picture
                user.profile.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
