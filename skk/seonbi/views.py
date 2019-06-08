import os
import uuid
import datetime
from django import forms
from django.conf import settings
from django.core import serializers
from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from seonbi.utils import current_millis
from seonbi.models import Video
from seonbi.tasks import upload_and_detect

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserForm, LoginForm
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.template import RequestContext

def index(request):
    if request.method == 'POST':
        uploaded = request.FILES.get('file')
        if uploaded is not None:
            ext = os.path.splitext(uploaded.name)[1]
            name = str(uuid.uuid4()) + '_' + str(current_millis())
            filename = name + ext
            filepath = default_storage.save(os.path.join(settings.MEDIA_ROOT, filename), request.FILES['file'])
            video = Video(status=Video.Status.UPLOADING, filename=uploaded.name)
            video.save()

            now = datetime.datetime.now()
            gcp_path = os.path.join('%d-%d-%d' % (now.year, now.month, now.day), filename)
            upload_and_detect.delay(video.id, filepath, gcp_path)
        return HttpResponseRedirect('/videos')
    return render(request, 'index.html', {})



def detail(request, video_id):
    return render(request, 'video_detail.html', {'video_id': video_id})


def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(**form.cleaned_data)
            login(request, new_user)
            return redirect('signin')
        else:
            return HttpResponse('회원가입 실패. 다시 시도 해보세요.')
    else:
        form = UserForm()
        return render(request, 'signup.html', {'form': form})


def signin(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        user_name = request.POST['username']
        pass_word = request.POST['password']
        user = authenticate(username = user_name, password = pass_word)
        if user is not None:
            login(request, user)
            return redirect('test')
        else:
            return HttpResponse('로그인 실패. 다시 시도 해보세요.')
    else:
        form = LoginForm()
        return render(request, 'signin.html', {'form': form})


def test(request):
    return render(request, 'test.html')

