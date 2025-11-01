from stegano import lsb
import cv2
import math
import os
import shutil
from subprocess import call, STDOUT
import aesutil
import rsautil1

def split_string(s_str, count=15):
    per_c = math.ceil(len(s_str) / count)
    c_cout = 0
    out_str = ''
    split_list = []
    for s in s_str:
        out_str += s
        c_cout += 1
        if c_cout == per_c:
            split_list.append(out_str)
            out_str = ''
            c_cout = 0
    if c_cout != 0:
        split_list.append(out_str)
    return split_list

def frame_extraction(video, temp_folder="tmp"):
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    print(f"[INFO] {temp_folder} directory is created")
    vidcap = cv2.VideoCapture(video)
    count = 0
    print("[INFO] Extracting frames from video... Please be patient.")
    while True:
        success, image = vidcap.read()
        if not success:
            break
        cv2.imwrite(os.path.join(temp_folder, f"{count}.png"), image)
        count += 1
    print("[INFO] All frames are extracted from video")
    return count

def clean_tmp(path="tmp"):
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"[INFO] {path} files are cleaned up")

def encode_process(video_path, message, encryption_style, key=None, key_path=None, frame_storage_image=None):
    temp_folder = "tmp_encode"
    clean_tmp(temp_folder)

    total_frames = frame_extraction(video_path, temp_folder)
    
    num_frames_needed = 15

    if num_frames_needed > total_frames:
        clean_tmp(temp_folder)
        raise ValueError(f"Not enough frames in the video. Needs {num_frames_needed}, but video only has {total_frames}.")

    frames = [int(i * (total_frames / (num_frames_needed + 1))) for i in range(1, num_frames_needed + 1)]
    frames = sorted(list(set(frames)))
    if len(frames) < num_frames_needed:
        frames = list(range(num_frames_needed))

    print(f"Auto-selected frames for encoding: {frames}")

    if encryption_style == 'AES':
        if not key:
            raise ValueError("AES encryption requires a key.")
        encrypted_string = aesutil.encrypt(key=key, source=message, keyType='ascii')

        if key_path:
            encrypted_aes_key = rsautil1.encrypt(message=key, key_path=key_path).decode('utf-8')
            print(f"Encrypted AES key: {encrypted_aes_key}")
        
        if frame_storage_image:
            frames_str = str(frames)
            encoded_frames_str = aesutil.encrypt(key=key, source=frames_str, keyType='ascii')
            secret = lsb.hide(frame_storage_image, str(encoded_frames_str))
            output_image_path = "image-enc.png"
            secret.save(output_image_path)
            print(f"[INFO] Frame numbers hidden in {output_image_path}")

    elif encryption_style == 'RSA':
        if not key_path:
            raise ValueError("RSA encryption requires a public key path.")
        encrypted_string = rsautil1.encrypt(message=message, key_path=key_path).decode('utf-8')

        if frame_storage_image:
            frames_str = str(frames)
            encoded_frames_str = rsautil1.encrypt(message=frames_str, key_path=key_path).decode('utf-8')
            secret = lsb.hide(frame_storage_image, str(encoded_frames_str))
            output_image_path = "image-enc.png"
            secret.save(output_image_path)
            print(f"[INFO] Frame numbers hidden in {output_image_path}")
    else:
        clean_tmp(temp_folder)
        raise ValueError("Invalid encryption style selected. Choose 'AES' or 'RSA'.")

    split_string_list = split_string(encrypted_string)

    for i, part in enumerate(split_string_list):
        frame_index = frames[i]
        frame_path = os.path.join(temp_folder, f"{frame_index}.png")
        secret_enc = lsb.hide(frame_path, part)
        secret_enc.save(frame_path)
        print(f"[INFO] Frame {frame_index} now holds a piece of the message.")

    output_video_path = "encoded_video.mov"
    audio_path = os.path.join(temp_folder, "audio.mp3")
    temp_video_path = os.path.join(temp_folder, "video.mov")

    call(["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)
    call(["ffmpeg", "-framerate", "30", "-i", os.path.join(temp_folder, "%d.png"), "-vcodec", "png", temp_video_path, "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)
    call(["ffmpeg", "-i", temp_video_path, "-i", audio_path, "-codec", "copy", output_video_path, "-y"], stdout=open(os.devnull, "w"), stderr=STDOUT)
    
    print(f"Video successfully encoded and saved to {output_video_path}")

    clean_tmp(temp_folder)

    result = {'video': output_video_path}
    if frame_storage_image:
        result['image'] = output_image_path
    if 'encrypted_aes_key' in locals():
        result['encrypted_aes_key'] = encrypted_aes_key

    return result
