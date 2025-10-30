from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm

from collections import OrderedDict

# taskhero/views.py
import json
import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import SavedPrompt, Task
from .forms import SavedPromptForm



# Create your views here.

def home_page(request):
    return render(request, "taskhero/home.html")


def about_page(request):
    # Handle logged-in and guest users safely
    if request.user.is_authenticated:
        # Get all tasks for the current user
        user_tasks = Task.objects.filter(owner=request.user).order_by('-created_at')[:6]  # recent 6 tasks
    else:
        user_tasks = None

    context = {
        "user_tasks": user_tasks,
    }

    return render(request, "taskhero/about.html", context)



# # 📖 Read (List all tasks)
# @login_required
# def task_list(request):
#     tasks = Task.objects.filter(owner=request.user).order_by('due_date')
#     return render(request, "taskhero/task_list.html", {"tasks": tasks})



PRIORITY_ORDER = ["HIGH", "MEDIUM", "LOW"]
STATUS_ORDER = ["TODO", "IN_PROGRESS", "COMPLETED", "CANCELLED"]

@login_required
def task_list(request):
    tasks_qs = Task.objects.filter(owner=request.user).order_by('-created_at')
    tasks = list(tasks_qs)

    def _p(t): return (t.priority or "").strip().upper()
    def _s(t): return (t.status or "").strip().upper()

    grouped_tasks = []
    handled_priorities = set()

    for pr in PRIORITY_ORDER:
        pr_tasks = [t for t in tasks if _p(t) == pr]
        if not pr_tasks:
            continue
        handled_priorities.add(pr)

        status_map = OrderedDict()
        for st in STATUS_ORDER:
            items = [t for t in pr_tasks if _s(t) == st]
            if items:
                status_map[st] = items

        for t in pr_tasks:
            st = _s(t) or "UNSPECIFIED"
            if st not in status_map:
                status_map.setdefault(st, []).append(t)

        statuses = []
        for st, items in status_map.items():
            statuses.append({
                "status": st,
                "status_label": st.replace("_", " ").title(),  # e.g. IN_PROGRESS -> In Progress
                "tasks": items
            })

        grouped_tasks.append({
            "priority": pr,
            "statuses": statuses
        })

    remaining_priorities = sorted({_p(t) for t in tasks if _p(t) and _p(t) not in handled_priorities})
    for pr in remaining_priorities:
        pr_tasks = [t for t in tasks if _p(t) == pr]
        status_map = OrderedDict()
        for t in pr_tasks:
            st = _s(t) or "UNSPECIFIED"
            status_map.setdefault(st, []).append(t)

        statuses = [{
            "status": st,
            "status_label": st.replace("_", " ").title(),
            "tasks": items
        } for st, items in status_map.items()]

        grouped_tasks.append({"priority": pr, "statuses": statuses})

    no_priority_tasks = [t for t in tasks if not _p(t)]
    if no_priority_tasks:
        status_map = OrderedDict()
        for t in no_priority_tasks:
            st = _s(t) or "UNSPECIFIED"
            status_map.setdefault(st, []).append(t)
        statuses = [{
            "status": st,
            "status_label": st.replace("_", " ").title(),
            "tasks": items
        } for st, items in status_map.items()]
        grouped_tasks.append({"priority": "UNSPECIFIED", "statuses": statuses})

    context = {"grouped_tasks": grouped_tasks}
    return render(request, "taskhero/task_list.html", context)







# ➕ Create
@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect('taskhero:task_list')
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
            return redirect('taskhero:task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, "taskhero/task_form.html", {"form": form, "title": "Edit Task"})

# ❌ Delete
@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        task.delete()
        return redirect('taskhero:task_list')
    return render(request, "taskhero/task_confirm_delete.html", {"task": task})




# 🧾 SIGN UP
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
            return redirect('taskhero:dashboard')
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
            return redirect('taskhero:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'auth/login.html')

# 🚪 LOGOUT
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You’ve been logged out successfully.")
    return redirect('taskhero:login')

# 📊 DASHBOARD (User’s Task Area)
@login_required
def dashboard_view(request):
    tasks = Task.objects.for_user(request.user)
    for i in tasks:
        print(i)
    return render(request, 'taskhero/dashboard.html', {'tasks': tasks})







@login_required
def generate_task_ai(request):
    if request.method == "POST":
        prompt = request.POST.get("prompt", "")
        user = request.user.username

        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",  # or mistral, phi3, etc.
            "prompt": f"Generate a list of tasks for user {user} based on: {prompt}. "
                      f"Each task should include a title, short description, priority, and status."
        }

        response = requests.post(ollama_url, json=payload, stream=True)
        output = ""
        for line in response.iter_lines():
            if line:
                data = line.decode("utf-8")
                if '"response":' in data:
                    output += data.split('"response":')[1].split('"')[1]

        return JsonResponse({"response": output.strip()})
    return render(request, "taskhero/generate_task_ai.html")





OLLAMA_API = "http://localhost:11434/api/generate"  # adjust if different
DEFAULT_MODEL = "llama3"

@login_required
def prompt_store_page(request):
    """
    Renders the page with editor + sidebar.
    The template will load prompts via the initial context or AJAX.
    """
    prompts = SavedPrompt.objects.filter(owner=request.user)
    # Optionally prefill with a default prompt
    default_prompt = "Generate a task with title, description, priority (HIGH/MEDIUM/LOW), status (TODO/IN_PROGRESS/COMPLETED), due_date YYYY-MM-DD."
    return render(request, "taskhero/prompt_store.html", {"prompts": prompts, "default_prompt": default_prompt})

@login_required
@require_POST
def save_prompt(request):
    """Create or update a prompt. POST JSON: {id(optional): int, title: str, prompt: str}"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    pid = payload.get("id")
    title = (payload.get("title") or "").strip()
    prompt_text = (payload.get("prompt") or "").strip()
    if not title or not prompt_text:
        return JsonResponse({"ok": False, "error": "Title and prompt are required"}, status=400)

    if pid:
        saved = get_object_or_404(SavedPrompt, pk=pid, owner=request.user)
        saved.title = title
        saved.prompt = prompt_text
        saved.save()
    else:
        saved = SavedPrompt.objects.create(owner=request.user, title=title, prompt=prompt_text)

    return JsonResponse({"ok": True, "prompt": {"id": saved.id, "title": saved.title, "prompt": saved.prompt, "updated_at": saved.updated_at.isoformat()}})

@login_required
@require_POST
def delete_prompt(request):
    """POST JSON: {id: int}"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
        pid = payload.get("id")
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)
    if not pid:
        return JsonResponse({"ok": False, "error": "id required"}, status=400)
    saved = get_object_or_404(SavedPrompt, pk=pid, owner=request.user)
    saved.delete()
    return JsonResponse({"ok": True})

@login_required
@require_POST
def run_prompt(request):
    """
    Run a prompt through Ollama and return the text. 
    POST JSON: {prompt: str, model(optional): str}
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
        prompt_text = payload.get("prompt", "").strip()
        model = payload.get("model", DEFAULT_MODEL)
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    if not prompt_text:
        return JsonResponse({"ok": False, "error": "Empty prompt"}, status=400)

    try:
        # call Ollama (simple approach)
        resp = requests.post(OLLAMA_API, json={"model": model, "prompt": prompt_text}, stream=False, timeout=20)
        resp.raise_for_status()
        # Ollama returns JSON or streaming chunks — handle simple JSON body
        try:
            data = resp.json()
            # If your Ollama output uses a key like 'response' or 'text', adapt accordingly
            if isinstance(data, dict):
                # Try common keys
                output = data.get("response") or data.get("text") or data.get("output") or json.dumps(data)
            else:
                output = str(data)
        except Exception:
            output = resp.text
    except Exception as e:
        # fallback: return error (or a simple local generator)
        return JsonResponse({"ok": False, "error": f"Ollama error: {str(e)}"}, status=500)

    return JsonResponse({"ok": True, "response": output})
