from django.urls import path
from . import views

app_name = "taskhero"

urlpatterns = [
    path("", views.home_page, name="home"),
    path("about/", views.about_page, name="about"),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/add/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('generate-ai/', views.generate_task_ai, name='generate_task_ai'),


    path('prompts/', views.prompt_store_page, name='prompt_store'),
    path('prompts/save/', views.save_prompt, name='prompt_save'),
    path('prompts/delete/', views.delete_prompt, name='prompt_delete'),
    path('prompts/run/', views.run_prompt, name='prompt_run'),
]