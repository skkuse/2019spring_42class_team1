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
from .models import Video


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
            vinfo = extract_video_info(filepath)

            # upload gcp
            client = storage.Client.from_service_account_json(settings.GCP_KEY_PATH)
            bucket = client.get_bucket(bucket_name)
            now = datetime.datetime.now()
            gcp_filepath = os.path.join('%d-%d-%d' % (now.year, now.month, now.day), filename)
            blob = Blob(gcp_filepath, bucket)
            blob.upload_from_filename(filepath)
            blob.make_public()
            url = gcp_url_format % (bucket_name, gcp_filepath)

            # TODO: extract frames and make censors using celery
            output_dir = os.path.join(os.path.dirname(filepath), name)
            os.makedirs(output_dir)
            extract_frames(filepath, output_dir, frame_size=(16 * 10, 9 * 10), interval_millis=10000)


            from nudenet import NudeClassifier
            classifier = NudeClassifier(settings.NUDE_NET_CLASSIFIER_MODEL_PATH)
            censors = dict()
            for frame_img in os.listdir(output_dir):
                frame_img_path = os.path.join(output_dir, frame_img)
                if not os.path.exists(frame_img_path) or os.path.isdir(frame_img_path):
                    continue
                nudity_prob = classifier.classify(frame_img_path).get(frame_img_path).get('nude')
                censors[frame_img] = str(nudity_prob)
            print(censors)
            return JsonResponse({'url': url, 'censors': censors})
    return render(request, 'index.html', {})
