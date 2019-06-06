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
from seonbi.tasks import upload_video, detect_scenes

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
            upload_video.delay(video.id, filepath, gcp_path)
            detect_scenes.delay(video.id, filepath)
        return HttpResponseRedirect('/videos')
    return render(request, 'index.html', {})
