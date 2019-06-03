from django import forms
from django.conf import settings
from django.core import serializers
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.template import loader
from django.shortcuts import render
from google.cloud import storage
from google.cloud.storage import Blob
import os
import uuid
from seonbi.utils import current_millis, extract_video_info, extract_frames
import datetime
from .models import Video, DetectedScene
from nudenet import NudeClassifier


bucket_name = 'seonbi'
gcp_url_format = 'http://storage.googleapis.com/%s/%s'

def index(request):
    if request.method == 'POST':
        uploaded = request.FILES.get('file')
        if uploaded is not None:
            ext = os.path.splitext(uploaded.name)[1]
            name = str(uuid.uuid4()) + '_' + str(current_millis())
            filename = name + ext
            filepath = default_storage.save(os.path.join(settings.MEDIA_ROOT, filename), request.FILES['file'])
            # vinfo = extract_video_info(filepath)

            now = datetime.datetime.now()
            gcp_path = os.path.join('%d-%d-%d' % (now.year, now.month, now.day), filename)
            url = upload_to_gcp(filepath, gcp_path)

            video = Video(status=Video.Status.UPLOADED, filename=uploaded.name, url=url)
            video.save()
            detected = detect(filepath, video)
            return JsonResponse({'url': url, 'scenes': list(map(lambda s: {'start_millis': s.start_millis, 'end_millis': s.end_millis}, detected))})
    return render(request, 'index.html', {})


def upload_to_gcp(src_path, gcp_path):
    client = storage.Client.from_service_account_json(settings.GCP_KEY_PATH)
    bucket = client.get_bucket(bucket_name)
    blob = Blob(gcp_path, bucket)
    blob.upload_from_filename(src_path)
    blob.make_public()
    return gcp_url_format % (bucket_name, gcp_path)


def frame_order(str):
    try:
        return int(os.path.splitext(str)[0].split('_')[1])
    except:
        return -1


def detect(src_path, video):
    frame_size = (160, 90)
    interval_millis = 1000
    classifier = NudeClassifier(settings.NUDE_NET_CLASSIFIER_MODEL_PATH)

    video.status = Video.Status.DETECTING

    src_name = os.path.splitext(os.path.basename(src_path))[0]
    output_dir = os.path.join(os.path.dirname(src_path), src_name)
    os.makedirs(output_dir)
    extract_frames(src_path, output_dir, frame_size, interval_millis)

    detected = list()
    thresold = 5 * interval_millis
    for frame in sorted(os.listdir(output_dir), key=lambda f: frame_order(f)):
        order = frame_order(frame)
        if order < 0:
            continue
        framepath = os.path.join(output_dir, frame) 
        if not os.path.exists(framepath) or os.path.isdir(framepath):
            continue
        result = classifier.classify(framepath)[framepath]
        nudity_prob = result['nude']
        if nudity_prob > 0.8:
            start_millis = order * interval_millis
            end_millis = (order + 1) * interval_millis
            if not detected:
                detected.append(DetectedScene(src_video=video, start_millis=start_millis, end_millis=1000, cause=DetectedScene.DetectionCause.NUDITY))
            else:
                latest = detected[-1]
                if latest.end_millis + thresold < latest.start_millis:
                    detected.append(DetectedScene(src_video=video, start_millis=start_millis, end_millis=1000, cause=DetectedScene.DetectionCause.NUDITY))
                else:
                    latest.end_millis = end_millis
    for scene in detected:
        scene.save()
    video.status = Video.Status.DETECTED
    return detected