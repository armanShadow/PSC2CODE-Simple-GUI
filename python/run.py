import os
from setting import *
from dbimpl import DBImpl
from preprocess import extract_frames, diff_frames
from video_tagging.predict import predict_video
from video_tagging.predict import load_model
from video import CVideo
from OCR.image_ocr import google_ocr
from OCR.adjust_ocr import GoogleOCRParser
from OCR.adjust_ocr import generate_doc
from util import *
import shutil
import json

def get_video_info(video_hash):
    db = DBImpl({'url': os.path.join(playlists_dir, 'videos.db')})
    sql = 'select title, playlist from videos where hash = ?'
    res = db.queryone(sql, video_hash)
    video_name = res[0].strip()
    video_playlist = res[1].strip()

    return [video_hash, video_name, video_playlist]

def checkOutDir(videoName):
    video = videoName.rsplit('.', 1)[0]
    if os.path.exists(os.path.join(out_dir, '%s.json'%video)):
        return "True"
    else: 
        return "False"

def extractingFrames(videoName):
    video = videoName.rsplit('.', 1)[0]
    video_mp4_path = os.path.join(video_dir, videoName)
    # preprocess
    os.mkdir(os.path.join(images_dir, video))
    extract_frames(video_mp4_path, os.path.join(images_dir, video))
    diff_frames(os.path.join(images_dir, video), thre=0.05, metric="NRMSE")

def predictValidFrames(videoName):
    video = videoName.rsplit('.', 1)[0]

    model = load_model(model_file)
    predict_video(os.path.join(images_dir, video), model)

def extractCodeRegions(videoName):
    video = videoName.rsplit('.', 1)[0]
    os.mkdir(os.path.join(lines_dir, video))
    cvideo = CVideo(video)
    # detect boundingx boxes and store the information of lines and rects into folder 'Lines'
    cvideo.cluster_lines()
    cvideo.adjust_lines()
    cvideo.detect_rects()
    # crop the bounding boxes of frames into folder 'Crops'
    cvideo.crop_rects()

def CorrectingErrors(videoName):
    video = videoName.rsplit('.', 1)[0]
    # OCR and the results are stored into folder 'GoogleOCR'
    google_ocr(video)

    os.mkdir(os.path.join(ocr_dir, video, "parse"))
    srt_file = os.path.join(video_dir, video+".srt")
    parser = GoogleOCRParser(video, srt_file)
    parser.correct_words()

    video_info = {}
    video_info['name'] = video
    video_info['frames'] = []

    for idx, doc in enumerate(parser.docs):

        if idx == len(parser.docs):
            continue

        frame = doc['frame']
        content = generate_doc(doc['lines'])
        display_time = second_to_str(doc['frame'])
        video_info['frames'].append([frame, content, display_time])

    with open(os.path.join(out_dir,'%s.json'%video), "w") as outfile:
        json.dump(video_info, outfile)

def deleteTempFiles(videoName):
    video = videoName.rsplit('.', 1)[0]

    if os.path.exists(os.path.join(images_dir, video)):
        shutil.rmtree(os.path.join(images_dir, video))

    if os.path.exists(os.path.join(lines_dir, video)):
        shutil.rmtree(os.path.join(lines_dir, video))

    if os.path.exists(os.path.join(crop_dir, video)):
        shutil.rmtree(os.path.join(crop_dir, video))

    if os.path.exists(os.path.join(ocr_dir, video)):
        shutil.rmtree(os.path.join(ocr_dir, video))


