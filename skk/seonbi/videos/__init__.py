import os
import uuid
import ffmpeg
import cv2
from django.conf import settings
from google.cloud import storage
from google.cloud.storage import Blob
from seonbi.utils import current_millis
from seonbi.models import Video, DetectedScene
from seonbi.errors import SourceNotFound
from nudenet import NudeClassifier

bucket_name = 'seonbi'
gcp_url_format = 'http://storage.googleapis.com/%s/%s'


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
    video.save()

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
    video.save()
    return detected


def extract_video_info(src_path):
    if not os.path.exists(src_path) or not os.path.isfile(src_path):
        raise SourceNotFound
    video = cv2.VideoCapture(src_path)
    fwidth, fheight = video.get(cv2.CAP_PROP_FRAME_WIDTH), video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video.get(cv2.CAP_PROP_FPS)
    num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    return {
        'width': fwidth,
        'height': fheight,
        'fps': fps,
        'num_frames': num_frames
    }

def extract_frames(src_path, outdir_path, frame_size, interval_millis=1000):
    if not os.path.exists(src_path) or not os.path.isfile(src_path):
        raise SourceNotFound
    src_name = str(uuid.uuid4()) + '_' + str(current_millis())
    cur_dir = os.path.dirname(src_path)
    out_dir = os.path.join(outdir_path, os.path.splitext(src_name)[0])

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    video = cv2.VideoCapture(src_path)
    print('###### start extracting frames: %s' % (src_path))
    fwidth, fheight = video.get(cv2.CAP_PROP_FRAME_WIDTH), video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video.get(cv2.CAP_PROP_FPS)
    num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    print('###### %d x %d, fps: %f, number of frames: %d' % (fwidth, fheight, fps, num_frames))

    cur_frame = 0
    while(True):
        # per a second
        video.set(cv2.CAP_PROP_POS_MSEC, cur_frame * interval_millis)
        ret, frame = video.read()
        if ret:
            frame_path = os.path.join(outdir_path, 'frame_' + str(cur_frame) + '.jpg')
            resized = cv2.resize(frame, (1280, 720))
            cv2.imwrite(frame_path, resized)
        else:
            break
        cur_frame += 1
        if cur_frame > num_frames / fps:
            break
    video.release()
    cv2.destroyAllWindows()
    print('###### extracting frames')
    print('###### from %s to %s complete.' % (src_path, out_dir))

