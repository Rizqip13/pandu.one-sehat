from django.shortcuts import render

# Create your views here.
def staff_dashboard(request):
    return render(request, "staff/dashboard.html")

def staff_file_list(request):
    return render(request, "staff/file_list.html")