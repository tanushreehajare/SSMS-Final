from django.shortcuts import render, HttpResponse, redirect
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash,authenticate, login as auth_login, logout, get_user_model
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from stationaryapp.models import facultyrequest, stationary, assignment, faculty, CustomUser, CustomUserManager,StationaryBill, item
from .forms import StationaryBillForm
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models.functions import Lower
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
from django.db.models import F, ExpressionWrapper, FloatField

CustomUser = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == "admin"
def is_faculty(user):
    return user.is_authenticated and user.role == "faculty"

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Log Out successful.")
    return redirect('/')

def aboutus(request):
    return render(request, 'registration/aboutus.html')

@login_required
def resetpassword(request):
    if request.method == 'POST':
        username = request.POST['username']
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            messages.error(request, "Username not found.")
            return render(request, 'admin/resetpassword.html')

        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            
            update_session_auth_hash(request, user)
            
            messages.success(request, "Password reset successful.")
            return redirect('/')
        else:
            messages.error(request, "Current password is incorrect.")

    return render(request, 'admin/resetpassword.html')

def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if user.role == "faculty":
                messages.success(request, "Login Successful!")
                return redirect('/facultylogin/')
            elif user.role == "admin":
                messages.success(request, "Login Successful!")
                return redirect('/adminlogin/')
        else:
            messages.error(request, "Invalid Credentials")
    else:
        pass
    return render(request, 'registration/login.html')

from google.auth.transport import requests
from google.oauth2 import id_token
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User

@csrf_exempt
def custom_login_redirect(request):
    if request.method == 'POST' or request.user.is_authenticated:
        # If the user is authenticated, proceed with the login
        if request.user.is_authenticated:
            email = request.user.email
        # If it's a POST request, extract email from the user's Google profile
        else:
            email = request.POST.get('email')
        
        if email.endswith('@somaiya.edu'):
            # Extract username from email
            username = email.split('@')[0]
            # Check if the user exists in the database
            try:
                user = CustomUser.objects.get(username=username, email=email)
                # Passing the backend argument explicitly
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, "Login Successful!")
                if user.role == "faculty":
                    return redirect('/facultylogin/')
                elif user.role == "admin":
                    return redirect('/adminlogin/')
                else:
                    messages.error(request, "User account is not valid.")
            except CustomUser.DoesNotExist:
                messages.error(request, "User does not exist.")
        else:
            messages.error(request, "Invalid email domain.")
    else:
        messages.error(request, "Invalid request method.")
    
    # Handle failed login attempts
    return redirect('login')

@login_required(login_url='login')
@user_passes_test(is_admin,login_url='login')
def reset_faculty_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")

        try:
            user = CustomUser.objects.get(username=username, role=CustomUser.FACULTY)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Faculty password reset successfully.")
            return redirect('/viewusers/')
        except CustomUser.DoesNotExist:
            messages.error(request, "Faculty with the provided username does not exist.")

    return render(request, "admin/resetfacultypassword.html", {'messages': messages.get_messages(request)})

@login_required(login_url='login')
@user_passes_test(is_faculty, login_url='login')
def facultypage(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            faculty_name = request.POST.get('faculty_name')
            faculty_gmail = request.POST.get('faculty_gmail')
            item_id = request.POST.get('item_dropdown')  
            quantity = request.POST.get('quantity')
            note = request.POST.get('note')
        
            if not (faculty_name and faculty_gmail and item_id and quantity and note):
                messages.error(request, "Please enter all details properly.")
            else:
                selected_item = item.objects.get(pk=item_id)  
                facultypage = facultyrequest(
                    faculty_name=faculty_name,
                    faculty_gmail=faculty_gmail,
                    item_name=selected_item,
                    quantity=quantity,
                    note=note,
                    request_date=datetime.today()
                )
                facultypage.save()
                messages.success(request, "Request Sent Successfully!")

        items = item.objects.annotate(lower_name=Lower('item_name')).order_by('lower_name')

        context = {
            'items': items,
        }
        return render(request, 'faculty/faculty_welcome_page.html', context)
        
@login_required
@user_passes_test(is_admin, login_url='login')
def delete_user(request, user_id):
    if request.user.is_authenticated:
        user_to_delete = CustomUser.objects.get(pk=user_id)
        if user_to_delete.role != CustomUser.ADMIN:
            user_to_delete.delete()
            messages.success(request, "User deleted successfully!")
        else:
            messages.error(request, "You cannot delete an admin user.")
    else:
        messages.error(request, "You need to be logged in to perform this action.")
    return redirect('view_users')

@login_required
@user_passes_test(is_admin, login_url='login')
def view_users(request):
    if request.user.is_authenticated:
        users = CustomUser.objects.all()
        return render(request, 'admin/view_users_page.html', {'users': users})
    else:
        messages.error(request, "Only admins can access this page.")
        return render(request, 'admin/view_users_page.html')

@login_required
@user_passes_test(is_admin, login_url='login')
def add_faculty_user(request):
    if request.method == "POST" and request.user.is_authenticated and request.user.is_superuser:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        branch = request.POST.get('branch')
        role = request.POST.get('role')
        
        # Extracting username from the email address
        username = email.split('@')[0]  # Get the part before the @ symbol
        
        if not email.endswith('@somaiya.edu'):
            messages.error(request, "Only @somaiya.edu email addresses are allowed.")
            return render(request, 'admin/add_faculty_page.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'admin/add_faculty_page.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'admin/add_faculty_page.html')

        my_user = CustomUser.objects.create_user(username=username, email=email, password=password)
        my_user.branch = branch
        my_user.first_name = first_name
        my_user.last_name = last_name
        
        if role == "admin":
            my_user.is_superuser = True
            my_user.is_staff = True
            my_user.role = CustomUser.ADMIN
        else:
            my_user.role = CustomUser.FACULTY
        
        my_user.save()

        messages.success(request, "User added successfully!")
    
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, "Only admins can access this page.")
    
    return render(request, 'admin/add_faculty_page.html')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def delete_assignment(request, assignment_id):
    if request.user.is_authenticated:
        try:
            assignment_instance = assignment.objects.get(pk=assignment_id)
            assignment_instance.delete()
            messages.success(request, "Assignment deleted successfully!")
        except assignment.DoesNotExist:
            messages.error(request, "Assignment does not exist.")
        messages.success(request, "Assignment deleted successfully!")
    else:
        messages.error(request, "Only admins can delete.")
    return redirect('VIEW_ASSIGNMENT')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def delete_faculty(request, faculty_id):
    if request.user.is_authenticated :
        Faculty = faculty.objects.get(pk=faculty_id)
        Faculty.delete()
        messages.success(request, "Faculty deleted successfully!")
    else:
        messages.error(request, "Only admins can delete.")
    return redirect('VIEW_FACULTY')

@login_required(login_url='login')
@user_passes_test(is_faculty, login_url='login')
def user_profile(request):
    user_profile = request.user
    return render(request, 'faculty/user_profile.html', {'user_profile': user_profile})

@login_required(login_url='login')
@user_passes_test(is_faculty, login_url='login')
def my_requests(request):
    if request.user.is_authenticated:
        faculty_requests = facultyrequest.objects.filter(faculty_gmail=request.user.email)
        
        context = {
            'faculty_requests': faculty_requests,
        }
    return render(request, 'faculty/view_my_requests.html', context)
    
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def admin_page(request):
    if request.user.is_authenticated:
        branch = request.user.branch
        user_count = CustomUser.objects.filter(branch=branch).count()
        stationeries = stationary.objects.all()
        available_stationery_count = sum(1 for s in stationeries if s.available_quantity > 0)
        pending_requests_count = facultyrequest.objects.exclude(status='Issued').count()
        context = {
            'user_count': user_count,
            'available_stationery_count': available_stationery_count,
            'pending_requests_count': pending_requests_count
        }

        return render(request, 'admin/admin_page.html', context)
    else:
        return render(request, 'admin/admin_page.html')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def stationary_and_faculty(request):
    if request.method == "POST":
        if "add_stationary" in request.POST:
            stationary_name = request.POST.get('item_dropdown')
            issued_quantity = int(request.POST.get('issued_quantity'))
            issued_date = request.POST.get('issue_date')
            issued_from = request.POST.get('issued_from')
            try:
                cost_per_item = Decimal(request.POST.get('cost_per_item', '0.00'))
            except InvalidOperation:
                messages.error(request, "Invalid cost_per_item value.")
            if not (stationary_name and issued_quantity and issued_date and issued_from and cost_per_item):
                
                messages.error(request, "Please enter all details properly.")
            else:
                selected_item = item.objects.get(pk=stationary_name)
                Stationary = stationary(stationary_name=selected_item, issued_quantity=issued_quantity,issued_date=issued_date,issued_from=issued_from, cost_per_item=cost_per_item)                                        
                Stationary.save()
                messages.success(request, "Stationary Added Successfully!")

        elif "add_faculty" in request.POST:
            facultys_name = request.POST.get('facultys_name')
            faculty_email = request.POST.get('faculty_email')
            if not (facultys_name and faculty_email):
                
                messages.error(request, "Please enter the faculty name.")
            else:
                
                existing_faculty = faculty.objects.filter(facultys_name=facultys_name, faculty_email=faculty_email).first()

                if existing_faculty:
                    
                    messages.error(request, "Faculty with this name already exists.")
                else:
                    
                    new_faculty = faculty(facultys_name=facultys_name,faculty_email=faculty_email)
                    new_faculty.save()
                    messages.success(request, "Faculty Added Successfully!")              
    items = item.objects.annotate(lower_name=Lower('item_name')).order_by('lower_name')

    context = {
        'items': items,
    }
    return render(request, 'admin/stationary_and_faculty.html', context)


from django.db.models import Sum, F, ExpressionWrapper, fields
from django.db.models import Max

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def assign_stationary(request):
    if request.method == "POST":
        faculty_name_id = request.POST.get('faculty_name')
        stationary_name = request.POST.get('stationary_name')
        assigned_quantity = int(request.POST.get('assigned_quantity'))
        assignment_date = request.POST.get('assignment_date')
        notes = request.POST.get('notes')
        if not (faculty_name_id and stationary_name and assigned_quantity and assignment_date and notes):
            messages.error(request, "Please enter all details properly.")
        else:
            faculty_name = faculty.objects.get(pk=faculty_name_id)
            # Modified to handle multiple objects with the same name
            stationary_items = stationary.objects.filter(stationary_name=stationary_name)
            if stationary_items.exists():
                available_quantity = stationary_items.first().available_quantity
                if assigned_quantity <= available_quantity:
                    assignment_item = assignment(
                        faculty_name=faculty_name,
                        stationary=stationary_items.first(),  # Take the first object
                        assigned_quantity=assigned_quantity,
                        assignment_date=assignment_date,
                        notes=notes
                    )
                    assignment_item.save()
                    messages.success(request, "Stationary Assigned Successfully!")
                else:
                    messages.error(request, "Not enough available quantity for the assignment.")
            else:
                messages.error(request, "Stationary not found.")
            return redirect('/assign_stationary/')
    faculty_requests = facultyrequest.objects.filter(status__in=['Pending', 'Seen', 'Ordered'])
    faculties = faculty.objects.all()
    stationaries = stationary.objects.values('stationary_name').distinct().order_by(Lower('stationary_name'))
    
    # Compute available quantity for each distinct stationary name
    stationary_data = []
    for item in stationaries:
        available_quantity = stationary.objects.filter(stationary_name=item['stationary_name']).first().available_quantity
        stationary_data.append({'name': item['stationary_name'], 'available_quantity': available_quantity})
    
    context = {
        'faculties': faculties,
        'stationaries': stationary_data,
        'faculty_requests': faculty_requests,
    }
    return render(request, 'admin/assign_stationary_page.html', context)



@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def view_requests(request):
    
    selected_status = request.GET.get('status_filter')

    faculty_requests = facultyrequest.objects.all().order_by('-id')

    if selected_status:
        faculty_requests = faculty_requests.filter(status=selected_status)

    if request.method == "POST":
        for faculty_request in faculty_requests:
            status = request.POST.get(f"status_{faculty_request.id}")
            if status:
                faculty_request.status = status
                faculty_request.save()
        
        return redirect('view_requests' + ('?status_filter=' + selected_status if selected_status else ''))

    context = {
        'faculty_requests': faculty_requests,
        'selected_status': selected_status, 
    }
    return render(request, 'admin/view_requests.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def update_status(request, request_id):
    if request.method == "POST":
        new_status = request.POST.get("status")
        faculty_request = facultyrequest.objects.get(id=request_id)
        faculty_request.status = new_status
        faculty_request.save()
        
        messages.success(request, 'Status updated successfully.') 
    return redirect('VIEW_FACULTY_REQUESTS')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def update_status_request(request, request_id):
    if request.method == "POST":
        new_status = request.POST.get("status")
        faculty_request = facultyrequest.objects.get(id=request_id)
        faculty_request.status = new_status
        faculty_request.save()
        
        messages.success(request, 'Status updated successfully.') 
    return redirect('ASSIGN_STATIONARY_TO_FACULTY')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def view_stationary(request):
       
    stationary_names = stationary.objects.all()
    stationary_names = stationary_names.order_by('id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_stationary = request.GET.get('stationary_name')
        
    filter_conditions = {}
    if selected_stationary:
        filter_conditions['stationary_name'] = selected_stationary
    if start_date:
        filter_conditions['issued_date__gte'] = start_date
    if end_date:
        filter_conditions['issued_date__lte'] = end_date
        
    stationary_names = stationary_names.annotate(
        total_cost=ExpressionWrapper(F('cost_per_item') * F('issued_quantity'), output_field=FloatField())
    )
        
    stationary_names = stationary_names.filter(**filter_conditions)
    unique_stationary_names = set(stationary_names.values_list('stationary_name', flat=True))
    unique_stationary_names = sorted(unique_stationary_names, key=lambda x: x.lower())

    context = {'stationary_names': stationary_names,'unique_stationary_names': unique_stationary_names}
    return render(request, 'admin/view_stationary_page.html', context )

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def view_faculty(request):
    faculty_names = faculty.objects.all().order_by('faculty_email')
    context = {'faculty_names': faculty_names}
    return render(request, 'admin/view_faculty_page.html', context )

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def view_assignments(request):
    assignments = assignment.objects.all()
    assignments = assignments.order_by('id')

    selected_faculty = request.GET.get('faculty')
    selected_stationary = request.GET.get('stationary')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    filter_conditions = {}
    if selected_faculty:
        filter_conditions['faculty_name'] = selected_faculty
    if selected_stationary:
        filter_conditions['stationary__stationary_name'] = selected_stationary
    if start_date:
        filter_conditions['assignment_date__gte'] = start_date
    if end_date:
        filter_conditions['assignment_date__lte'] = end_date

    assignments = assignments.filter(**filter_conditions)

    unique_faculty_names = set(assignments.values_list('faculty_name', flat=True))
    unique_stationary_names = set(assignments.values_list('stationary__stationary_name', flat=True))
    unique_stationary_names = sorted(unique_stationary_names, key=lambda x: x.lower())
    
    context = {
        'assignment_names': assignments,
        'unique_faculty_names': unique_faculty_names,
        'unique_stationary_names': unique_stationary_names,
    }
    return render(request, 'admin/view_assignment_page.html', context)

@require_POST
@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def generate_pdf_report(request):
    selected_faculty = request.POST.get('faculty')
    selected_stationary = request.POST.get('stationary')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    filter_conditions = {}
    if selected_faculty:
        filter_conditions['faculty_name'] = selected_faculty
    if selected_stationary:
        filter_conditions['stationary__stationary_name'] = selected_stationary
    if start_date:
        filter_conditions['assignment_date__gte'] = start_date
    if end_date:
        filter_conditions['assignment_date__lte'] = end_date

    assignments = assignment.objects.filter(**filter_conditions)

    styles = getSampleStyleSheet()

    elements = []

    img_path = "static/images/letterhead.png"
    image = Image(img_path, width=600, height=120)
    image.hAlign = 'CENTER'
    image.vAlign = 'TOP'
    elements.append(image)
    
    heading = Paragraph("<div align='center'><font size='16'><b>Department Of Artificial Intelligence And Data Science</b></font></div>", styles['Normal'])

    elements.append(heading)
    
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    
    table_data = [
        ['Sr. No.', 'Faculty Name', 'Stationary Name', 'Quant.', 'Assign-Date','Note', 'Remark']
    ]
    for index, assignment_item in enumerate(assignments, start=1):
        assignment_date_formatted = assignment_item.assignment_date.strftime('%d-%m-%Y') if assignment_item.assignment_date else ''
        table_data.append([
            index,
            assignment_item.faculty_name,
            assignment_item.stationary.stationary_name,
            assignment_item.assigned_quantity,
            assignment_date_formatted,  # Formatted date
            assignment_item.notes,
            ''
        ])

    table = Table(table_data)
    style = TableStyle([
       ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8), 
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    table.setStyle(style)
    elements.append(table)

    hod_name_text = Paragraph("<div align='right'>Dr. M.U. Nemade<br/>&nbsp;&nbsp;&nbsp;<b>HOD AI&amp;DS</b></div>", styles['Normal'])
    elements.append(Spacer(1, 50))
    elements.append(hod_name_text)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=20)
    doc.build(elements)

    return response

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def edit_stationary(request):
    if request.method == 'POST':
        for stationary_item in stationary.objects.all():
            stationary_id = str(stationary_item.id)
            stationary_name = request.POST.get('stationary_name_' + stationary_id)
            ordered_quantity = request.POST.get('ordered_quantity_' + stationary_id)
            issued_date = request.POST.get('issued_date_' + stationary_id)
            issued_from = request.POST.get('issued_from_' + stationary_id)
            cost_per_item = request.POST.get('cost_per_item_' + stationary_id)
            
            stationary_item.stationary_name = stationary_name
            stationary_item.issued_quantity = ordered_quantity
            # Do not set available_quantity directly
            # stationary_item.available_quantity = available_quantity
            stationary_item.issued_date = issued_date
            stationary_item.issued_from = issued_from
            stationary_item.cost_per_item = cost_per_item
            stationary_item.save()
        messages.success(request, "Stationary updated successfully")
    stationary_names = stationary.objects.all()
    context = {'stationary_names': stationary_names}
    return render(request, 'admin/edit_stationary_page.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def delete_stationary(request, stationary_id):
    if request.user.is_authenticated :
        stationary_item = stationary.objects.get(pk=stationary_id)
        stationary_item.delete()
        messages.success(request, "stationary deleted successfully!")
    else:
        messages.error(request, "Only admins can delete stationary.")
    return redirect('edit_stationary')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def addProduct(request):
    if request.method == "POST":
        prod = StationaryBill()
        prod.created_at = request.POST.get('created_at')
        prod.caption = request.POST.get('caption')

        if len(request.FILES) != 0:
            prod.image = request.FILES['image']

        prod.save()
        messages.success(request, "Image Added Successfully")
        return redirect('bill_feed')
    return render(request, 'admin/add.html')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def image_feed(request):
    images = StationaryBill.objects.all().order_by('-created_at')
    return render(request, 'admin/image_feed.html', {'images': images})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def deleteProduct(request, pk):
    prod = StationaryBill.objects.get(id=pk)
    if prod.image:
        os.remove(prod.image.path)
    prod.delete()
    messages.success(request,"Image Deleted Successfully")
    return redirect('bill_feed')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def add_item(request):
    if request.method == "POST":
        item_name = request.POST.get('item_name')
        
        if not item_name:
            messages.error(request, "Please enter the item name.")
        else:
            if item.objects.filter(item_name=item_name).exists():
                messages.error(request, "Item with this name already exists.")
            else:
                new_item = item(item_name=item_name)
                new_item.save()
                messages.success(request, "Item Added Successfully!")
                return redirect('view_items')  
    messages.success(request, "Item Added Successfully!")
    return render(request, 'admin/add_item.html')

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def view_items(request):
    items = item.objects.order_by(Lower('item_name'))
    context = {'items': items}
    return render(request, 'admin/view_items.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def delete_item(request, item_id):
    if request.user.is_authenticated :
        Item = item.objects.get(pk=item_id)
        Item.delete()
        messages.success(request, "Item deleted successfully!")
    else:
        messages.error(request, "Only admins can delete.")
    return redirect('view_items')

@login_required(login_url='login')
@user_passes_test(is_faculty, login_url='login')
def my_assignments(request):
    if request.user.is_authenticated:
        faculty_user = faculty.objects.get(faculty_email=request.user.email)
        assignments = assignment.objects.filter(faculty_name=faculty_user.facultys_name)
        assignments = assignments.order_by('-id')
        selected_stationary = request.GET.get('stationary')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        filter_conditions = {}
        if selected_stationary:
            filter_conditions['stationary__stationary_name'] = selected_stationary
        if start_date:
            filter_conditions['assignment_date__gte'] = start_date
        if end_date:
            filter_conditions['assignment_date__lte'] = end_date
            
        assignments = assignments.filter(**filter_conditions)
        unique_stationary_names = set(assignments.values_list('stationary__stationary_name', flat=True))
        unique_stationary_names = sorted(unique_stationary_names, key=lambda x: x.lower())
        
        return render(request, 'faculty/myassignments.html', {'assignments': assignments, 'faculty_user': faculty_user,'unique_stationary_names': unique_stationary_names})
    else:
        return render(request, 'registration/login.html', {})
    
from .models import Profile
from .helpers import send_forget_password_mail
import uuid
import os 

def forgetpassword(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')

            # Check if the user exists
            if not CustomUser.objects.filter(username=username).exists():  
                messages.error(request, 'User does not exist.')
                return redirect('login')
            
            # Generate a token and update the user's profile
            user_obj = CustomUser.objects.get(username=username)  
            token = str(uuid.uuid4())
            
            profile_obj, _ = Profile.objects.get_or_create(user=user_obj)
            profile_obj.forget_password_token = token
            profile_obj.save()
            
            # Send password reset email
            send_forget_password_mail(user_obj.email, token)
            messages.success(request, 'A password reset email has been sent.')
            return redirect('forget_password')
    except Exception as e:
        # Handle any exceptions gracefully
        messages.error(request, 'An error occurred while processing your request. Please try again later.')
        # Optionally, log the exception for debugging purposes
        # logger.error(f"Error in forgetpassword: {e}")

    return render(request, 'registration/forgetpassword.html')


def changepassword(request, token):
    context = {}
    try:
        profile_obj = Profile.objects.filter(forget_password_token=token).first()
        if not profile_obj:
            context['validlink'] = False  # Invalid token
        else:
            context['validlink'] = True  # Valid token
            context['user_id'] = profile_obj.user.id
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('reconfirm_password')
            user_id = request.POST.get('user_id')
            
            if not user_id:
                messages.error(request, 'User Not Found')
                return redirect(f'/change_password/{token}/')
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords Do Not Match')
                return redirect(f'/change_password/{token}/')
            
            user_obj = CustomUser.objects.get(id=user_id) 
            user_obj.set_password(new_password)
            user_obj.save()
            messages.success(request, 'Password Changed Successfully. Please Log In.')
            return redirect('login')
        
    except Exception as e:
        print(e)
        messages.error(request, 'An error occurred while processing your request. Please try again later.')
    return render(request, 'faculty/changepassword.html', context)


#excel files

def insights(request):
    return render(request, 'ds/insyt.html')

def top_stationaries_data(request):
    stationaries = stationary.objects.annotate(
        assigned_sum=Sum('assignment__assigned_quantity')
    ).order_by('-assigned_sum')[:10]

    data = {
        'labels': [stationary.stationary_name for stationary in stationaries],
        'ordered_quantity': [stationary.overall_issued_quantity or 0 for stationary in stationaries],
        'assigned_quantity': [stationary.assigned_sum or 0 for stationary in stationaries]
    }
    return JsonResponse(data)

def top_assigned_stationaries_data(request):
    stationaries = stationary.objects.annotate(
        assigned_sum=Sum('assignment__assigned_quantity')
    ).order_by('-assigned_sum')[:10]

    data = {
        'labels': [stationary.stationary_name for stationary in stationaries],
        'assigned_quantity': [stationary.assigned_sum or 0 for stationary in stationaries]
    }
    return JsonResponse(data)

def request_status_data(request):
    status_counts = facultyrequest.objects.values('status').annotate(count=Count('status'))
    data = {
        'labels': [entry['status'] for entry in status_counts],
        'counts': [entry['count'] for entry in status_counts],
        'colors': {
            'Issued': 'rgba(75, 192, 192, 0.5)',   # green
            'Ordered': 'rgba(54, 162, 235, 0.5)',  # blue
            'Pending': 'rgba(255, 99, 132, 0.5)',  # red
            'Seen': 'rgba(255, 206, 86, 0.5)'      # yellow
        }
    }
    return JsonResponse(data)

def status_counts(request):
    data = facultyrequest.objects.values('status').annotate(count=Count('status'))
    status_data = {
        'labels': [item['status'] for item in data],
        'counts': [item['count'] for item in data]
    }
    return JsonResponse(status_data)

def top_requested_items(request):
    # Aggregate request counts by item_name
    item_requests = facultyrequest.objects.values('item_name').annotate(count=Count('item_name')).order_by('-count', 'request_date')[:10]

    # Get the available quantities for these top 10 items
    item_names = [item['item_name'] for item in item_requests]
    items = stationary.objects.filter(stationary_name__in=item_names)
    
    item_quantities = {item.stationary_name: item.available_quantity for item in items}

    data = {
        'labels': [item['item_name'] for item in item_requests],
        'counts': [item['count'] for item in item_requests],
        'available_quantities': [item_quantities[item['item_name']] for item in item_requests]
    }
    
    return JsonResponse(data)

def available_years(request):
    # Get all years with data
    years_with_data = assignment.objects.annotate(year=TruncYear('assignment_date')).values('year').annotate(count=Count('id')).order_by('year')
    
    # Extract years
    years = [year['year'].year for year in years_with_data]

    return JsonResponse({'years': years})

def assignment_data_by_month(request, year):
    # Get all months
    all_months = {month: 0 for month in range(1, 13)}

    # Get assignments data
    data = assignment.objects.filter(assignment_date__year=year).annotate(month=TruncMonth('assignment_date')).values('month').annotate(count=Count('id')).order_by('month')

    # Populate assignment data
    for item in data:
        month = item['month'].month
        all_months[month] = item['count']

    response_data = {
        'months': [calendar.month_name[month] for month in all_months.keys()],  # Use full month names
        'counts': list(all_months.values())
    }
    return JsonResponse(response_data)

import calendar
import pandas as pd
from django.db.models import Count
from django.http import JsonResponse
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment
from io import BytesIO
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear

def generate_excel_response(df, filename):
    wb = Workbook()
    ws = wb.active

    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    for column in ws.columns:
        max_length = 0
        column_name = column[0].column_letter
        for cell in column:
            if isinstance(cell.value, pd.Timestamp):
                cell.number_format = 'YYYY-MM-DD'
                cell.alignment = Alignment(horizontal='center')
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_name].width = adjusted_width

    # Save the workbook to a BytesIO object
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# Views for downloading data
def download_stationary_data(request):
    data = stationary.objects.all().values()
    df = pd.DataFrame(list(data))
    return generate_excel_response(df, 'stationary_data.xlsx')

def download_assignment_data(request):
    data = assignment.objects.all().values()
    df = pd.DataFrame(list(data))
    return generate_excel_response(df, 'assignment_data.xlsx')

def download_faculty_request_data(request):
    data = facultyrequest.objects.all().values()
    df = pd.DataFrame(list(data))
    return generate_excel_response(df, 'faculty_request_data.xlsx')
