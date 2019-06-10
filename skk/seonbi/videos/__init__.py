import os
import uuid
import ffmpeg
import cv2
import shutil
from django.conf import settings
from google.cloud import storage
from google.cloud.storage import Blob
from seonbi.utils import current_millis
from seonbi.models import Video, DetectedScene
from seonbi.errors import SourceNotFound
from nudenet import NudeClassifier, NudeDetector

bucket_name = 'seonbi'

def gcp_path(url):
    return url.replace('https://storage.googleapis.com/seonbi/', '').replace('http://storage.googleapis.com/seonbi/', '')


def upload_to_gcp(src_path, gcp_path):
    print('###### start upload from %s to %s' % (src_path, gcp_path))
    client = storage.Client.from_service_account_json(settings.GCP_KEY_PATH)
    bucket = client.get_bucket(bucket_name)
    blob = Blob(gcp_path, bucket)
    blob.upload_from_filename(src_path)
    blob.make_public()
    print('##### upload success: %s' % blob.public_url)
    return blob.public_url


def delete_gcp_file(url):
    print('###### start removing %' % url)
    client = storage.Client.from_service_account_json(settings.GCP_KEY_PATH)
    bucket = client.get_bucket(bucket_name)
    blob = Blob(gcp_path(url), bucket)
    blob.delete()
    print('###### removing success %' % url)


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
    thresold = 3 * interval_millis
    print('start detecting %d files' % (len(os.listdir(output_dir))))
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
                detected.append(DetectedScene(src_video=video, start_millis=start_millis, end_millis=end_millis, cause=DetectedScene.DetectionCause.NUDITY))
            else:
                latest = detected[-1]
                if latest.end_millis + thresold <= start_millis:
                    detected.append(DetectedScene(src_video=video, start_millis=start_millis, end_millis=end_millis, cause=DetectedScene.DetectionCause.NUDITY))
                else:
                    latest.end_millis = end_millis
    print('the number of detected scenes is %d' % len(detected))
    for scene in detected:
        scene.save()
    video.status = Video.Status.DETECTED
    video.save()
    try:
        shutil.rmtree(output_dir)
    except Exception as e:
        print('fail to remove directory', e)
    return detected


def filter(fr, scenes, removal):
    video = fr.src_video
    fileext = os.path.splitext(os.path.basename(video.url))[1]
    src_name = str(uuid.uuid4()) + '_' + str(current_millis())
    src_path = os.path.join(settings.MEDIA_ROOT, src_name + fileext)
    print('##### start download  %s' % src_path)
    client = storage.Client.from_service_account_json(settings.GCP_KEY_PATH)
    bucket = client.get_bucket(bucket_name)
    blob = Blob(gcp_path(video.url), bucket)
    blob.download_to_filename(src_path)
    print('##### complete download %s' % src_path)

    out_name = str(uuid.uuid4()) + '_' + str(current_millis())
    out_path = os.path.join(settings.MEDIA_ROOT, out_name + fileext)
    infile = ffmpeg.input(src_path)
    if removal:
        print('##### start removing scenes')
        remove_op = []
        for scene in scenes:
            remove_op.append(
                infile.trim(start=scene['start_millis'] / 1000, end=scene['end_millis']).setpts('N/FR/TB')
            )
        if len(remove_op) > 0:
            ffmpeg.concat(remove_op).output(src_path).run(overwrite_output=True)
    else:
        # extract frames for detecting
        print('##### start extracting frames for detecting blurbox')
        detector = NudeDetector(settings.NUDE_NET_DETECTOR_MODEL_PATH)
        frames_dir = os.path.join(settings.MEDIA_ROOT, src_name)
        if not os.path.exists(frames_dir):
            os.makedirs(frames_dir)
        try:
            video = cv2.VideoCapture(src_path)
            fps = video.get(cv2.CAP_PROP_FPS)
            num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
            duration =  int((num_frames / fps) * 1000)
            interval = 250
            for scene in scenes:
                cur_millis = scene['start_millis']
                while (True):
                    video.set(cv2.CAP_PROP_POS_MSEC, cur_millis)
                    ret, frame = video.read()
                    if ret:
                        frame_path = os.path.join(frames_dir, str(cur_millis) + '.jpg')
                        cv2.imwrite(frame_path, frame)
                    else:
                        break
                    cur_millis += interval
                    if cur_millis >= scene['end_millis'] or cur_millis > duration:
                        print(cur_millis, scene['end_millis'], duration)
                        break
            print('##### complete extracting frames for detecting blurbox')
            print('##### start detecting blurbox %s' % frames_dir)
            for frame in sorted(os.listdir(frames_dir), key=lambda f: int(os.path.splitext(f)[0])):
                censors = detector.detect(os.path.join(frames_dir, frame))
                print('detected blur box point %d from %s' % (len(censors), frame))
                start_millis = int(os.path.splitext(frame)[0])
                for censor in censors:
                    if not censor['label'] is 'F_BREAST':
                        continue
                    blurbox = censor['box']
                    infile.overlay(
                        infile.crop(x=blurbox[0], y=blurbox[1], width=blurbox[2] - blurbox[0], height=blurbox[3] - blurbox[1]).filter_('boxblur', luma_radius=10, luma_power=10),
                        x=blurbox[0],
                        y=blurbox[1],
                        enable='between(t, %d, %d)' % (start_millis / 1000, start_millis + interval / 1000)
                    )
            print('##### complete detecting blurbox')
            video.release()
            cv2.destroyAllWindows()
            infile.output(out_path).run(overwrite_output=True)
            os.remove(src_path)
            shutil.rmtree(frames_dir)
        except Exception as e:
            print('##### detect and blur failed %s', str(e))
            os.remove(src_path)
            shutil.rmtree(frames_dir)
            raise e
            
    return out_path


def extract_frames(src_path, outdir_path, frame_size, interval_millis=1000):
    if not os.path.exists(src_path) or not os.path.isfile(src_path):
        raise SourceNotFound
    src_name = str(uuid.uuid4()) + '_' + str(current_millis())
    cur_dir = os.path.dirname(src_path)
    if not os.path.exists(outdir_path):
        os.makedirs(outdir_path)

    video = cv2.VideoCapture(src_path)
    print('###### start extracting frames: %s' % (src_path))
    fwidth, fheight = video.get(cv2.CAP_PROP_FRAME_WIDTH), video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video.get(cv2.CAP_PROP_FPS)
    num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    print('###### %d x %d, fps: %f, the number of frames: %d' % (fwidth, fheight, fps, num_frames))

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
    print('###### extracting frames complete from %s to %s complete.' % (src_path, outdir_path))
