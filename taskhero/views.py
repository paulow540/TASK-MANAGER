from django.shortcuts import render, HttpResponse

# Create your views here.

def home_page(request):

    return render(request, "taskhero/home.html")



