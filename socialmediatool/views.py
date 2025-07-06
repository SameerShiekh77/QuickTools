from django.shortcuts import render

# Create your views here.
def brand_kit(request):
    """
    Render the brand kit page.
    """
    return render(request, 'socialmediatool/brand-kit.html')