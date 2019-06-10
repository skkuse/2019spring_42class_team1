from django.db import models


class Video(models.Model):
    class Status:
        # gcp upload
        UPLOADING = 'UPLOADING'
        UPLOADED = 'UPLOADED'
        # detect scenes
        DETECTING = 'DETECTING'
        DETECTED = 'DETECTED'
        FAILED = 'FAILED'
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20)
    thumbnail = models.TextField(null=True)
    filename = models.TextField()
    url = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DetectedScene(models.Model):
    class DetectionCause:
        NUDITY = 'NUDITY'
        SWEAR = 'SWEAR'    # 욕설
    id = models.AutoField(primary_key=True)
    thumbnail = models.TextField(null=True)
    src_video = models.ForeignKey(Video, on_delete=models.CASCADE)
    start_millis = models.BigIntegerField()
    end_millis = models.BigIntegerField()
    cause = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)


class FilteredResult(models.Model):
    class Status:
        FILTERING = 'FILTERING'
        UPLOADING = 'UPLOADING'
        COMPLETE = 'COMPLETE'
        FAILED = 'FAILED'
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20)
    src_video = models.ForeignKey(Video, on_delete=models.CASCADE)
    url = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
