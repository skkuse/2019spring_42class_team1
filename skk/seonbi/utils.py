import time
import cv2
import os
import sys
import re

def current_millis():
    return int(time.time() * 1000)

import uuid
from seonbi.errors import SourceNotFound

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
