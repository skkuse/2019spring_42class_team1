from django import forms
from django.conf import settings
from django.core import serializers
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.template import loader
from django.shortcuts import render
from .models import User
import os


class SignUpForm(forms.Form):
    email = forms.CharField(max_length=30)
    password = forms.CharField(max_length=20)


def index(request):
    if request.method == 'POST':
        uploaded = request.FILES.get('file')
        if uploaded is not None:
            save_path = os.path.join(settings.MEDIA_ROOT, uploaded.name)
            path = default_storage.save(save_path, request.FILES['file'])
            return JsonResponse({'path': path})
    return render(request, 'index.html', {})


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            new_user = User(email=form.email, password=form.password)
            new_user.save()
            return JsonResponse(serializers.serialize('json', new_user))
    return render(request, 'signup.html', {})


def sign_in(request):
    return render(request, 'signin.html', {})
