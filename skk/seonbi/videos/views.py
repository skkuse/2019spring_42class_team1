from django.core import serializers
from django.shortcuts import render
from seonbi.models import Video


def index(request):
    return render(request, 'videos.html', { 'videos': Video.objects.all() })


def detail(request, video_id):
    return render(request, 'video_detail.html', {})
