from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task
from .models import SavedPrompt

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'status', 'priority']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']




class SavedPromptForm(forms.ModelForm):
    class Meta:
        model = SavedPrompt
        fields = ["title", "prompt"]
        widgets = {
            "title": forms.TextInput(attrs={"class":"w-full p-2 border rounded", "placeholder":"Short title"}),
            "prompt": forms.Textarea(attrs={"class":"w-full p-2 border rounded", "rows":6, "placeholder":"Write the prompt..."}),
        }
