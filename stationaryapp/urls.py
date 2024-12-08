from django.urls import path
from stationaryapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('resetpassword/', views.resetpassword, name='resetpassword'),
    path('reset_faculty_password/', views.reset_faculty_password, name='reset_faculty_password'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('add_faculty_user/', views.add_faculty_user, name='ADDUSERS'),
    path('viewusers/', views.view_users, name='view_users'),
    path('deleteuser/<int:user_id>/', views.delete_user, name='delete_user'),
    path('user_profile/', views.user_profile, name='PROFILE'),
    path('view_my_requests/', views.my_requests, name='my_requests'),
    path('adminlogin/', views.admin_page, name='STATIONARY_MANAGEMENT_SYSTEM'),
    path('facultylogin/', views.facultypage, name='FACULTY_REQUEST_PAGE'),
    path('add_stationary_faculty/', views.stationary_and_faculty, name='STATIONARY_AND_FACULTY_MANAGEMENT_SYSTEM'),
    path('assign_stationary/', views.assign_stationary, name='ASSIGN_STATIONARY_TO_FACULTY'),
    path('view_requests/', views.view_requests, name='VIEW_FACULTY_REQUESTS'),
    path('view_stationary/', views.view_stationary, name='VIEW_STATIONARY'),
    path('view_faculty/', views.view_faculty, name='VIEW_FACULTY'),
    path('view_assignments/', views.view_assignments, name='VIEW_ASSIGNMENT'),
    path('generate_pdf_report/', views.generate_pdf_report, name='generate_pdf_report'),
    path('billinvoice/', views.image_feed, name='bill_feed'),
    path('update_stationary/', views.edit_stationary, name='edit_stationary'),
    path('delete_stationary/<int:stationary_id>/', views.delete_stationary, name='delete_stationary'),
    path('delete_assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
    path('delete_faculty/<int:faculty_id>/', views.delete_faculty, name='delete_faculty'),
    path('update_status/<int:request_id>/', views.update_status, name='update_status'),
    path('update_status_request/<int:request_id>/', views.update_status_request, name='update_status_request'),
    path('add_items/', views.add_item, name='add_item'),
    path('view_items/', views.view_items, name='view_items'),
    path('delete_item/<int:item_id>/', views.delete_item, name='delete_item'),
    path('myassignments/', views.my_assignments, name='MY_ASSIGNMENT'),
    path('add-product/', views.addProduct, name="add-prod"),
    path('delete_product/<int:pk>/', views.deleteProduct, name='delete_product'),

    path('forget_password/', views.forgetpassword, name='forget_password'),
    path('change_password/<token>/', views.changepassword, name='change_password'),
    
    path('insights/', views.insights, name='insights'),
    path('top-stationaries-data/', views.top_stationaries_data, name='top_stationaries_data'),
    path('top_assigned_stationaries_data/', views.top_assigned_stationaries_data, name='top_assigned_stationaries_data'),
    path('status_counts/', views.status_counts, name='status_counts'),
    path('assignment_data_by_month/<int:year>/', views.assignment_data_by_month, name='assignment_data_by_month'),
    path('available_years/', views.available_years, name='available_years'),
    path('top-requested-items/', views.top_requested_items, name='top_requested_items'),
    
    path('download/stationary/', views.download_stationary_data, name='download_stationary_data'),
    path('download/assignment/', views.download_assignment_data, name='download_assignment_data'),
    path('download/faculty_request/', views.download_faculty_request_data, name='download_faculty_request_data'),
]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
