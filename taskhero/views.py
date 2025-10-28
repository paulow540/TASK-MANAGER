from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm



# Create your views here.

def home_page(request):
    return render(request, "taskhero/home.html")


def about_page(request):
    # Get the current logged-in user safely
    myuser = get_object_or_404(User, username=request.user.username)

    context = {
        "user_tasks": myuser,
    }

    return render(request, "taskhero/about.html", context)




# 📖 Read (List all tasks)
@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user).order_by('due_date')
    return render(request, "taskhero/task_list.html", {"tasks": tasks})

# ➕ Create
@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, "taskhero/task_form.html", {"form": form, "title": "Add Task"})

# ✏️ Update
@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, "taskhero/task_form.html", {"form": form, "title": "Edit Task"})

# ❌ Delete
@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        task.delete()
        return redirect('task_list')
    return render(request, "taskhero/task_confirm_delete.html", {"task": task})




# 🧾 SIGN UP
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'auth/signup.html', {'form': form})

# 🔐 LOGIN
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'auth/login.html')

# 🚪 LOGOUT
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You’ve been logged out successfully.")
    return redirect('login')

# 📊 DASHBOARD (User’s Task Area)
@login_required
def dashboard_view(request):
    tasks = Task.objects.for_user(request.user)
    for i in tasks:
        print(i)
    return render(request, 'taskhero/dashboard.html', {'tasks': tasks})