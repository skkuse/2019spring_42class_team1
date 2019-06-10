from django.http import JsonResponse
from seonbi.models import Video, DetectedScene, FilteredResult
from seonbi.tasks import delete_video, filter_and_upload

def video_detail(request, video_id):
    if request.method == 'DELETE':
        return delete(request, video_id)
    if request.method == 'POST':
        return filter(request, video_id, request.POST.get("scene_ids", list()))
    return get_video_detail(request, video_id)


def filter_detail(request, video_id, filter_id):
    result = FilteredResult.objects.get(id=filter_id)
    return JsonResponse({
        'id': result.id,
        'status': result.status,
        'url': url,
        'created_at': created_at
    })


def get_video_detail(request, video_id):
    video = Video.objects.get(id = video_id)
    detected_scenes = DetectedScene.objects.filter(src_video = video).values()
    return JsonResponse({
        'video': {
            'status': video.status,
            'filename': video.filename,
            'url': video.url,
            'created_at': video.created_at
        },
        'detected_scenes': [
            {'id': scene['id'], 'start_millis': scene['start_millis'], 'end_millis': scene['end_millis'], 'cause': scene['cause']} for scene in detected_scenes
        ]
    })


def delete(request, video_id):
    video = Video.objects.get(id = video_id)
    try:
        delete_video.delay(video.url)
    except:
        print('failed')
    video.delete()
    return JsonResponse({})


def filter(request, video_id, scene_ids):
    video = Video.objects.get(id=video_id)
    fr = FilteredResult(status=FilteredResult.Status.FILTERING, src_video=video)
    fr.save()
    filter_and_upload.delay(fr.id, [], removal=False)
    return JsonResponse({
        'id': fr.id,
        'status': fr.status
    })
