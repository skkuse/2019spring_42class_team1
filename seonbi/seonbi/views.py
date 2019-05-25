from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.template import loader
from django.shortcuts import render
from django import forms
from django.conf import settings
import os

class UploadFileForm(forms.Form):
    # title = forms.CharField(max_length=50)
    file = forms.FileField()

def index(request):
    if request.method == 'POST':
        uploaded = request.FILES.get('file')
        if uploaded is not None:
            save_path = os.path.join(settings.MEDIA_ROOT, uploaded.name)
            path = default_storage.save(save_path, request.FILES['file'])
            return JsonResponse({'path': path})
        else:
            form = UploadFileForm()
    return render(request, 'index.html', {})
