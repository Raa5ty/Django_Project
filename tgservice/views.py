from django.shortcuts import render

# Create your views here.
def main_view(request):
    return render(request, "tgservice/index.html", context={})