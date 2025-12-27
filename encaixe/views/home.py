from django.shortcuts import render

def index(request):
    """
    Renders the main menu / dashboard of the application.
    """
    return render(request, 'encaixe/index.html')
