from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver


# ==================== CUSTOM USER MODEL ====================

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.email


# ==================== LOOKUP TABLES ====================

class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Provinces"
        ordering = ['name']


class Municipality(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='municipalities')

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['name', 'province']
        verbose_name_plural = "Municipalities"
        ordering = ['name']


class Barangay(models.Model):
    name = models.CharField(max_length=100)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='barangays')

    def __str__(self):
        return f"{self.name}, {self.municipality.name}"

    class Meta:
        unique_together = ['name', 'municipality']
        ordering = ['name']


class BarangayTransect(models.Model):
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name='barangay_transects')
    shallow_start_lat = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    shallow_start_lng = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    shallow_end_lat = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    shallow_end_lng = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    deep_start_lat = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    deep_start_lng = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    deep_end_lat = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    deep_end_lng = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    source = models.CharField(max_length=20, choices=[
        ('manual', 'Manually Added'),
        ('assessment', 'Created from Assessment'),
    ], default='manual')
    assessment = models.ForeignKey('Assessment', null=True, blank=True, on_delete=models.SET_NULL, related_name='saved_transect_coords')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Coords for {self.barangay.name} (#{self.pk})"

    class Meta:
        ordering = ['barangay', 'pk']


class Species(models.Model):
    SOURCE_MANUAL = 'manual'
    SOURCE_ASSESSMENT = 'assessment'
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, 'Manually Added'),
        (SOURCE_ASSESSMENT, 'Created from Assessment'),
    ]

    sub_category = models.CharField(max_length=200, help_text="e.g. ACROPORA BRANCHING (ACB)")
    major_category = models.CharField(max_length=200, help_text="Family, e.g. ACROPORIDAE")
    code = models.CharField(max_length=20, blank=True, help_text="Short code extracted from name")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)

    def __str__(self):
        return f"{self.sub_category} ({self.major_category})"

    class Meta:
        verbose_name_plural = "Species"
        unique_together = ['sub_category', 'major_category']
        ordering = ['major_category', 'sub_category']

    def save(self, *args, **kwargs):
        if not self.code and '(' in self.sub_category:
            import re
            match = re.search(r'\(([^)]+)\)', self.sub_category)
            if match:
                self.code = match.group(1).strip()
        super().save(*args, **kwargs)


# ==================== ASSESSMENT MODELS ====================

class Assessment(models.Model):
    METHODOLOGY_CHOICES = (
        ('photo_quadrat', 'Photo-Quadrat Survey'),
        ('line_transect', 'Line Transect'),
        ('point_intercept', 'Point Intercept'),
    )

    CONDITION_CHOICES = (
        ('poor', 'Poor'),
        ('fair', 'Fair'),
        ('good', 'Good'),
        ('excellent', 'Excellent'),
    )

    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name='assessments')
    barangay = models.ForeignKey(Barangay, on_delete=models.PROTECT, related_name='assessments')
    assessment_date = models.DateField()
    methodology = models.CharField(max_length=100, default='photo_quadrat')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True, null=True)
    overall_coral_cover = models.DecimalField(max_digits=7, decimal_places=4, blank=True, null=True, help_text="Final Mean coral cover %")
    thesis_pdf = models.FileField(upload_to='assessments/thesis/', blank=True, null=True)
    description = models.TextField(blank=True, null=True, help_text="Brief description of the assessment")
    contributors = models.ManyToManyField('Contributor', blank=True, related_name='assessments')
    notes = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assessments')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_assessments')
    approved_at = models.DateTimeField(blank=True, null=True, help_text="When the assessment was approved")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.barangay} - {self.assessment_date}"

    def get_methodology_display_name(self):
        for val, label in self.METHODOLOGY_CHOICES:
            if self.methodology == val:
                return label
        return self.methodology

    class Meta:
        ordering = ['-assessment_date', '-created_at']

    def compute_condition(self):
        if self.overall_coral_cover is None:
            return
        cover = float(self.overall_coral_cover)
        if cover < 10:
            self.condition = 'poor'
        elif cover < 25:
            self.condition = 'fair'
        elif cover < 50:
            self.condition = 'good'
        else:
            self.condition = 'excellent'


class Transect(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='transects')
    transect_number = models.PositiveIntegerField()

    # Shallow location + excel
    shallow_start_lat = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    shallow_start_lng = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    shallow_end_lat = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    shallow_end_lng = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    shallow_excel = models.FileField(upload_to='assessments/transect_excel/', blank=True, null=True)

    # Deep location + excel
    deep_start_lat = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    deep_start_lng = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    deep_end_lat = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    deep_end_lng = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    deep_excel = models.FileField(upload_to='assessments/transect_excel/', blank=True, null=True)

    def __str__(self):
        return f"Transect {self.transect_number} ({self.assessment})"

    @property
    def depth_health(self):
        """Return per-depth health dict: {shallow: {label, color, avg}, deep: {label, color, avg}}."""
        result = {}
        for depth_label in ('shallow', 'deep'):
            records = self.species_data.filter(depth=depth_label)
            if not records.exists():
                result[depth_label] = {'label': 'Unknown', 'color': '#6b7280', 'avg': 0}
                continue
            avg = sum(float(r.cover) for r in records) / records.count()
            if avg >= 65:
                result[depth_label] = {'label': 'Excellent', 'color': '#16a34a', 'avg': avg}
            elif avg >= 45:
                result[depth_label] = {'label': 'Good', 'color': '#2563eb', 'avg': avg}
            elif avg >= 25:
                result[depth_label] = {'label': 'Fair', 'color': '#d97706', 'avg': avg}
            else:
                result[depth_label] = {'label': 'Poor', 'color': '#dc2626', 'avg': avg}
        return result

    def _health_for_depth(self, depth_label):
        records = self.species_data.filter(depth=depth_label)
        if not records.exists():
            return {'label': 'Unknown', 'color': '#6b7280', 'avg': 0}
        avg = sum(float(r.cover) for r in records) / records.count()
        if avg >= 65:
            return {'label': 'Excellent', 'color': '#16a34a', 'avg': avg}
        elif avg >= 45:
            return {'label': 'Good', 'color': '#2563eb', 'avg': avg}
        elif avg >= 25:
            return {'label': 'Fair', 'color': '#d97706', 'avg': avg}
        return {'label': 'Poor', 'color': '#dc2626', 'avg': avg}

    @property
    def shallow_health(self):
        return self._health_for_depth('shallow')

    @property
    def deep_health(self):
        return self._health_for_depth('deep')

    @property
    def overall_health(self):
        """Return overall health for this transect combining both depth zones."""
        info = self.depth_health
        values = [v for v in info.values() if v['label'] != 'Unknown']
        if not values:
            return {'label': 'Unknown', 'color': '#6b7280', 'avg': 0}
        avg = sum(v['avg'] for v in values) / len(values)
        if avg >= 65:
            return {'label': 'Excellent', 'color': '#16a34a', 'avg': avg}
        elif avg >= 45:
            return {'label': 'Good', 'color': '#2563eb', 'avg': avg}
        elif avg >= 25:
            return {'label': 'Fair', 'color': '#d97706', 'avg': avg}
        else:
            return {'label': 'Poor', 'color': '#dc2626', 'avg': avg}

    class Meta:
        unique_together = ['assessment', 'transect_number']
        ordering = ['transect_number']


class TransectSpecies(models.Model):
    DEPTH_CHOICES = (
        ('shallow', 'Shallow'),
        ('deep', 'Deep'),
    )

    transect = models.ForeignKey(Transect, on_delete=models.CASCADE, related_name='species_data')
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='transect_data')
    depth = models.CharField(max_length=10, choices=DEPTH_CHOICES)
    cover = models.DecimalField(max_digits=7, decimal_places=4, default=0)

    def __str__(self):
        return f"{self.species.code} - T{self.transect.transect_number} ({self.depth})"

    class Meta:
        unique_together = ['transect', 'species', 'depth']
        ordering = ['depth', 'species__major_category', 'species__sub_category']


class AssessmentImage(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='assessments/images/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Assessment #{self.assessment.id} - {self.caption or 'No caption'}"

    class Meta:
        ordering = ['uploaded_at']


# ==================== CONTRIBUTOR MODEL ====================

class Contributor(models.Model):
    first_name = models.CharField(max_length=150)
    middle_initial = models.CharField(max_length=1, blank=True, default='')
    last_name = models.CharField(max_length=150)
    suffix = models.CharField(max_length=20, blank=True, default='')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contributor_profile')

    def get_full_name(self):
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_initial:
            parts.append(f"{self.middle_initial}.")
        if self.last_name:
            parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return ' '.join(parts) if parts else ''

    def __str__(self):
        return self.get_full_name() or 'Unnamed Contributor'

    class Meta:
        ordering = ['last_name', 'first_name']


# ==================== CUSTOM METHODOLOGY ====================

class CustomMethodology(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# ==================== USER PROFILE ====================

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('curator', 'Curator'),
        ('contributor', 'Contributor'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='contributor')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    middle_initial = models.CharField(max_length=1, blank=True, default='')
    suffix = models.CharField(max_length=20, blank=True, default='')
    bio = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    profile_completed = models.BooleanField(
        default=True,
        help_text='False for users who signed in with Google and still need to fill in their name details.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_full_name(self):
        parts = []
        if self.user.first_name:
            parts.append(self.user.first_name)
        if self.middle_initial:
            parts.append(f"{self.middle_initial}.")
        if self.user.last_name:
            parts.append(self.user.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return ' '.join(parts) if parts else ''
    
    def __str__(self):
        return f"{self.get_full_name() or self.user.email} - {self.get_role_display()} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-approve admin and curator roles (they don't need approval)
        if self.role in ['admin', 'curator']:
            self.status = 'approved'
        super().save(*args, **kwargs)
    
    class Meta:
        permissions = [
            ("can_manage_users", "Can manage users"),
            ("can_curate_content", "Can curate content"),
            ("can_contribute", "Can contribute content"),
            ("can_approve_users", "Can approve user registrations"),
        ]

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile for every new user.
    - Superusers: Admin role, auto-approved
    - Admin-created users: Auto-approved (handled in form)
    - Self-registered users: Pending approval
    """
    if created:
        if instance.is_superuser:
            role = 'admin'
            status = 'approved'
        else:
            role = 'contributor'
            status = 'pending'
        
        UserProfile.objects.create(user=instance, role=role, status=status)


class Notification(models.Model):
    TYPE_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned to Pending'),
        ('info', 'Information'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    assessment = models.ForeignKey('Assessment', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}: {self.title}"

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile whenever the User is saved.
    """
    if hasattr(instance, 'profile'):
        if instance.is_superuser and instance.profile.role != 'admin':
            instance.profile.role = 'admin'
            instance.profile.status = 'approved'
            instance.profile.save()
        instance.profile.save()


class SecurityAuditLog(models.Model):
    """Immutable audit trail for security-relevant events."""

    EVENT_CHOICES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('login_locked', 'Login Locked Out'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('account_created', 'Account Created'),
        ('account_approved', 'Account Approved'),
        ('account_rejected', 'Account Rejected'),
        ('account_deactivated', 'Account Deactivated'),
        ('assessment_approved', 'Assessment Approved'),
        ('assessment_rejected', 'Assessment Rejected'),
        ('assessment_deleted', 'Assessment Deleted'),
        ('user_role_changed', 'User Role Changed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='audit_logs'
    )
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'anonymous'
        return f'[{self.event}] {user_str} @ {self.created_at:%Y-%m-%d %H:%M}'


