import json
import seonbi.tasks as task
from django.http import JsonResponse
from seonbi.models import Video, DetectedScene, FilteredResult


def video_detail(request, video_id):
    if request.method == 'DELETE':
        return delete_video(request, video_id)
    if request.method == 'POST':
        return filter_video(request, video_id, request.POST.getlist('scene_ids', list()), json.loads(request.POST.get('removal', 'false')))
    return get_video_detail(request, video_id)


def filter_detail(request, video_id, filter_id):
    if request.method == 'DELETE':
        return delete_filter(request, video_id, filter_id)
    result = FilteredResult.objects.get(id=filter_id)
    return JsonResponse({
        'id': result.id,
        'status': result.status,
        'url': result.url,
        'created_at': result.created_at
    })


def get_video_detail(request, video_id):
    video = Video.objects.get(id=video_id)
    detected_scenes = DetectedScene.objects.filter(src_video=video).values()
    filtered_results = FilteredResult.objects.filter(src_video=video).values()
    return JsonResponse({
        'video': {
            'status': video.status,
            'filename': video.filename,
            'url': video.url,
            'created_at': video.created_at
        },
        'filtered_results': [
            {'id': fr['id'], 'status': fr['status'], 'url': fr['url'], 'created_at': fr['created_at']} for fr in filtered_results
        ],
        'detected_scenes': [
            {'id': scene['id'], 'start_millis': scene['start_millis'], 'end_millis': scene['end_millis'], 'cause': scene['cause']} for scene in detected_scenes
        ]
    })


def delete_video(request, video_id):
    video = Video.objects.get(id=video_id)
    try:
        task.delete_video.delay(video.url)
    except:
        print('deleting video in gcp failed')
    video.delete()
    return JsonResponse({})


def delete_filter(request, video_id, filter_id):
    fr = FilteredResult.objects.get(id=filter_id)
    try:
        task.delete_video.delay(fr.url)
    except:
        print('deleting video in gcp failed')
    fr.delete()
    return JsonResponse({})


def filter_video(request, video_id, scene_ids, removal):
    video = Video.objects.get(id=video_id)
    fr = FilteredResult(
        status=FilteredResult.Status.FILTERING, src_video=video)
    fr.save()
    task.filter_and_upload.delay(fr.id, scene_ids, removal)
    return JsonResponse({
        'id': fr.id,
        'status': fr.status
    })
