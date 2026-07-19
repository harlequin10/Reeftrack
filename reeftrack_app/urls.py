from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('assessment/<int:assessment_id>/', views.public_assessment_detail, name='public_assessment_detail'),
    path('explore/', views.public_dashboard, name='public_dashboard'),
    path('api/public/dashboard-data/', views.public_dashboard_data, name='public_dashboard_data'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('curator-dashboard/', views.curator_dashboard, name='curator_dashboard'),
    path('contributor-dashboard/', views.contributor_dashboard, name='contributor_dashboard'),
    
    # Admin Management URLs
    path('manage/users/', views.admin_manage_users, name='admin_manage_users'),
    path('manage/users/create/', views.admin_create_user, name='admin_create_user'),
    path('manage/users/edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('manage/users/action/<int:user_id>/', views.admin_user_action, name='admin_user_action'),
    
    # Curator Management URLs
    path('curator/manage-contributors/', views.curator_manage_contributors, name='curator_manage_contributors'),
    path('curator/contributor/action/<int:user_id>/', views.curator_contributor_action, name='curator_contributor_action'),
    path('curator/contributor/edit/<int:user_id>/', views.curator_edit_contributor, name='curator_edit_contributor'),
    
    # ==================== ASSESSMENT URLs ====================
    path('assessment/upload/', views.upload_assessment, name='upload_assessment'),
    path('assessment/add-transect/', views.add_transect, name='add_transect'),
    path('assessment/confirm-duplicate/', views.confirm_duplicate, name='confirm_duplicate'),
    path('assessment/preview/', views.preview_assessment, name='preview_assessment'),
    path('assessment/confirm/', views.confirm_assessment, name='confirm_assessment'),
    path('assessment/my-assessments/', views.my_assessments, name='my_assessments'),
    path('assessment/<int:assessment_id>/detail/', views.contributor_assessment_detail, name='contributor_assessment_detail'),
    path('assessment/<int:assessment_id>/delete/', views.delete_assessment, name='delete_assessment'),
    path('api/transect-suggestions/', views.get_transect_suggestions, name='transect_suggestions'),
    path('api/check-reference-match/', views.check_reference_match, name='check_reference_match'),
    path('api/species-suggestions/', views.get_species_suggestions, name='species_suggestions'),
    path('api/barangays/', views.get_barangays, name='get_barangays'),
    path('api/contributors/search/', views.search_contributors, name='search_contributors'),
    path('api/contributors/create/', views.create_contributor, name='create_contributor'),

    # ==================== ADMIN ASSESSMENT REVIEW ====================
    path('manage/assessments/', views.admin_assessments, name='admin_assessments'),
    path('manage/assessments/<int:assessment_id>/', views.admin_assessment_detail, name='admin_assessment_detail'),
    path('manage/assessments/<int:assessment_id>/confirm-approval/', views.admin_confirm_approval, name='admin_confirm_approval'),
    path('manage/assessments/<int:assessment_id>/action/', views.admin_assessment_action, name='admin_assessment_action'),

    # ==================== ADMIN LOCATION MANAGEMENT ====================
    path('manage/locations/', views.admin_manage_locations, name='admin_manage_locations'),
    path('manage/locations/bulk-delete/', views.admin_bulk_delete_municipalities, name='admin_bulk_delete_municipalities'),
    path('manage/locations/add-municipality/', views.admin_add_municipality, name='admin_add_municipality'),
    path('manage/locations/<int:municipality_id>/edit/', views.admin_edit_municipality, name='admin_edit_municipality'),
    path('manage/locations/<int:municipality_id>/delete/', views.admin_delete_municipality, name='admin_delete_municipality'),
    path('manage/locations/<int:municipality_id>/barangays/', views.admin_manage_barangays, name='admin_manage_barangays'),
    path('manage/locations/<int:municipality_id>/barangays/bulk-delete/', views.admin_bulk_delete_barangays, name='admin_bulk_delete_barangays'),
    path('manage/locations/<int:municipality_id>/barangays/add/', views.admin_add_barangay, name='admin_add_barangay'),
    path('manage/locations/barangays/<int:barangay_id>/edit/', views.admin_edit_barangay, name='admin_edit_barangay'),
    path('manage/locations/barangays/<int:barangay_id>/delete/', views.admin_delete_barangay, name='admin_delete_barangay'),

    # ==================== ADMIN SPECIES MANAGEMENT ====================
    path('manage/species/', views.admin_manage_species, name='admin_manage_species'),
    path('manage/species/add-family/', views.admin_add_family, name='admin_add_family'),
    path('manage/species/family/', views.admin_manage_family_species, name='admin_manage_family_species'),
    path('manage/species/family/<str:family_name>/add/', views.admin_add_species, name='admin_add_species_in_family'),
    path('manage/species/<int:species_id>/edit/', views.admin_edit_species, name='admin_edit_species'),
    path('manage/species/<int:species_id>/delete/', views.admin_delete_species, name='admin_delete_species'),
    path('manage/species/family/<str:family_name>/delete/', views.admin_delete_family, name='admin_delete_family'),

    # ==================== ADMIN TRANSECT COORDINATE MANAGEMENT ====================
    path('manage/transect-coords/', views.admin_manage_transect_coords, name='admin_manage_transect_coords'),
    path('manage/transect-coords/<int:barangay_id>/', views.admin_barangay_transect_coords, name='admin_barangay_transect_coords'),

    # ==================== CURATOR ASSESSMENT REVIEW ====================
    path('curator/assessments/', views.curator_assessments, name='curator_assessments'),
    path('curator/assessments/<int:assessment_id>/', views.curator_assessment_detail, name='curator_assessment_detail'),
    path('curator/assessments/<int:assessment_id>/confirm-approval/', views.curator_confirm_approval, name='curator_confirm_approval'),
    path('curator/assessments/<int:assessment_id>/action/', views.curator_assessment_action, name='curator_assessment_action'),

    # ==================== NEW PROFILE URLs ====================
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.profile_change_password, name='profile_change_password'),
]