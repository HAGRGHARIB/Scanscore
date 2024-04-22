from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import StudentRegistrationForm, TeacherRegistrationForm
from .models import Exam, ExamSubmission
from .forms import ExamForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect



def index(request):
    return render(request, 'myapp/index.html')



def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Instead of logging in the user, redirect to the login page
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')  # Redirect to the login page
        else:
            print("Form errors:", form.errors)  # Debug form errors
    else:
        form = StudentRegistrationForm()
    return render(request, 'myapp/student/register_student.html', {'form': form})

def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Instead of logging in the user, redirect to the login page
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')  # Redirect to the login page
    else:
        form = TeacherRegistrationForm()
    return render(request, 'myapp/teacher/register_teacher.html', {'form': form})



def login_view(request):
    print("CSRF Token from form:", request.POST.get('csrfmiddlewaretoken'))
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print("Username:", username)
        print("Password:", password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.userType == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'myapp/login.html')


def logout_view(request):
    logout(request)
    return render(request, 'myapp/index.html')

def student_dashboard(request):
    if not hasattr(request.user, 'student'): # Check if the user is a student
        return HttpResponseForbidden("You are not authorized to view this page.")
    student_submissions = ExamSubmission.objects.filter(student=request.user)
    return render(request, 'myapp/student/student_dashboard.html', {'student_submissions': student_submissions})




def teacher_dashboard(request):
    if not hasattr(request.user, 'teacher'): # Check if the user is a teacher
        return HttpResponseForbidden("You are not authorized to view this page.")
    exams = Exam.objects.filter(teacher=request.user)
    return render(request, 'myapp/teacher/teacher_dashboard.html', {'exams': exams})


def create_exam(request):
    if not hasattr(request.user, 'teacher'):
        return HttpResponseForbidden("You are not authorized to view this page.")
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.teacher = request.user
            exam.save()
            messages.success(request, 'Exam created successfully.')
            return redirect('teacher_dashboard')
    else:
        form = ExamForm()
    return render(request, 'myapp/teacher/create_exam.html', {'form': form})




def view_exam(request, exam_id):
    exam = Exam.objects.get(pk=exam_id)
    if not (request.user == exam.teacher or hasattr(request.user, 'teacher')):
        return HttpResponseForbidden("You are not authorized to view this exam.")
    return render(request, 'myapp/teacher/view_exam.html', {'exam': exam})


@login_required
def take_exam(request):
    search_query = request.GET.get('search', '')  # Get the search term from the URL
    # Filter the exams for which the student has not submitted answers
    submitted_exams = ExamSubmission.objects.filter(student=request.user).values_list('exam', flat=True) #Exams that the student has submitted
    if search_query:
        exams = Exam.objects.filter(is_active=True, name__icontains=search_query).exclude(pk__in=submitted_exams)
    else:
        exams = Exam.objects.filter(is_active=True).exclude(pk__in=submitted_exams)
    return render(request, 'myapp/student/take_exam.html', {'exams': exams})



@login_required
def enter_exam(request, exam_id): #this will redirect to the specific exam page where the student can take the exam
    exam = get_object_or_404(Exam, pk=exam_id, is_active=True)
    return render(request, 'myapp/student/enter_specific_exam.html', {'exam': exam})

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == 'POST':
        student_answer = request.POST.get('student_answer')
        # Save the submission
        ExamSubmission.objects.create(
            exam=exam,
            student=request.user,
            student_answer=student_answer,
            score=0, #Not graded yet
        )
        # Redirect to the student dashboard
        return redirect('student_dashboard')
    


@login_required
def view_profile_student(request):

    return render(request, 'myapp/student/view_profile.html', {'user': request.user})



@login_required
def edit_profile_student(request):
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        student_id = request.POST.get('student_id')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        print("Retrieved data:", first_name, last_name, student_id, email, username, password)

        # Update user's profile data
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username

        if password:  # Check if password was provided
            user.set_password(password)
            user.save()
            print("User is saved with password")
            # Re-authenticate user after password change
            updated_user = authenticate(username=username, password=password)
            if updated_user:
                login(request, updated_user)
                print("Now logged in as :", updated_user.username)
                messages.success(request, 'Profile updated successfully.')
                return redirect('view_profile_student')
    else:
        messages.error(request, "There was an error updating your profile. Please try again.")
        return redirect('edit_profile_student')
        

@login_required
def view_profile_teacher(request):
    return render(request, 'myapp/teacher/view_profile.html', {'user': request.user})

@login_required
def edit_profile_teacher(request):
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        print("Retrieved data:", first_name, last_name, email, username, password)

        # Update user's profile data
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username

        if password:
            user.set_password(password)
            user.save()
            print("User is saved with password")

            # Re-authenticate user after password change
            updated_user = authenticate(username=username, password=password)
            if updated_user:
                login(request, updated_user)
                print("Now logged in as :", updated_user.username)
                messages.success(request, 'Profile updated successfully.')
                return redirect('view_profile_teacher')
    else:
        messages.error(request, "There was an error updating your profile. Please try again.")
        return redirect('edit_profile_teacher')
    

@login_required
@login_required
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)  # Ensure that only the teacher who created the exam can edit it
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)  # Pass instance on POST to update the specific exam
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully.')
            return redirect('view_exam', exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)  # Initialize form with instance data on GET (to hold the current data in the form)
    return render(request, 'myapp/teacher/edit_exam.html', {'form': form, 'exam': exam})



@login_required
def publish_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)  # Ensure that only the teacher who created the exam can publish it
    if request.method == 'POST':
        exam.is_active = True
        exam.save()
        messages.success(request, "Exam published successfully.")
        return redirect(reverse('view_exam', args=[exam.id]))
    else:
        return HttpResponseForbidden("Invalid request")


@login_required
def unpublish_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)
    if request.method == 'POST':
        exam.is_active = False
        exam.save()
        messages.success(request, "Exam unpublished successfully.")
        return redirect('view_exam', exam_id=exam.id)
    else:
        return HttpResponseForbidden("Invalid request")



@login_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, "Exam deleted successfully.")
        return HttpResponseRedirect(reverse('teacher_dashboard')) # Redirect to the teacher dashboard
    else:
        return HttpResponseForbidden("Invalid request")


# @login_required
# def view_submissions(request, exam_id):
#     exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)
#     submissions = ExamSubmission.objects.filter(exam=exam)
#     return render(request, 'myapp/teacher/view_submissions.html', {'submissions': submissions, 'exam': exam})

@login_required
def view_submissions(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)
    submissions = ExamSubmission.objects.filter(exam=exam)
    is_graded = all(submission.is_graded for submission in submissions)
    
    if is_graded:
        print("All submissions are graded , so redirecting to view_grades")
        return render(request, 'myapp/teacher/view_grades.html', {'submissions': submissions, 'exam': exam})
    else:
        print("Submissions are not graded , so redirecting to view_submissions")
        return render(request, 'myapp/teacher/view_submissions.html', {'submissions': submissions, 'exam': exam})

@login_required
def view_grades(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, teacher=request.user)
    submissions = ExamSubmission.objects.filter(exam=exam)
    return render(request, 'myapp/teacher/view_grades.html', {'submissions': submissions, 'exam': exam})


@login_required
def modify_grade(request, submission_id):
    if request.method == 'POST':
        new_grade = request.POST.get('new_grade')
        submission = get_object_or_404(ExamSubmission, id=submission_id, exam__teacher=request.user)
        submission.score = int(new_grade)
        submission.save()
        messages.success(request, "Grade updated successfully.")
        return redirect('view_grades', exam_id=submission.exam.id)  # Redirect back to the submissions list
    return HttpResponseForbidden("Invalid request")


