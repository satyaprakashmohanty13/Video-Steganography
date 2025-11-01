from stegano import lsb
import cv2
import os
import shutil
import aesutil
import rsautil1
import ast

def clean_tmp(path="tmp"):
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"[INFO] {path} files are cleaned up")

def decode_process(encoded_video_path, decryption_style, encoded_image_path=None, frames_input=None, key=None, rsa_key_path=None):
    temp_folder = "tmp_decode"
    clean_tmp(temp_folder)
    os.makedirs(temp_folder)

    frames = []

    if encoded_image_path:
        try:
            encrypted_frames_str = lsb.reveal(encoded_image_path)
            if not encrypted_frames_str:
                raise ValueError("No hidden message found in the image.")

            print(f"Encrypted frame numbers from image: {encrypted_frames_str}")

            if decryption_style == 'AES':
                if not key:
                    raise ValueError("An AES key is required to decrypt frame numbers.")
                decrypted_frames_str = aesutil.decrypt(key=key, source=encrypted_frames_str, keyType='ascii').decode('utf-8')
            elif decryption_style == 'RSA':
                if not rsa_key_path:
                    raise ValueError("An RSA private key is required to decrypt frame numbers.")
                decrypted_frames_str = rsautil1.decrypt(message=encrypted_frames_str, key_path=rsa_key_path).decode('utf-8')
            else:
                raise ValueError("Unsupported decryption type for frame numbers.")

            frames = ast.literal_eval(decrypted_frames_str)
            print(f"Decrypted frames: {frames}")

        except Exception as e:
            clean_tmp(temp_folder)
            raise RuntimeError(f"Failed to decode frames from image: {e}")

    elif frames_input:
        try:
            frames = [int(f.strip()) for f in frames_input.split(',')]
        except ValueError:
            raise ValueError("Frames must be a comma-separated list of numbers.")
    else:
        raise ValueError("Either an encoded image or manual frame numbers must be provided.")

    cap = cv2.VideoCapture(encoded_video_path)
    if not cap.isOpened():
        clean_tmp(temp_folder)
        raise IOError("Could not open the encoded video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")

    decoded_parts = {}
    frame_number = -1

    while frame_number < total_frames:
        frame_number += 1
        ret, frame = cap.read()
        if not ret:
            break
        if frame_number in frames:
            frame_path = os.path.join(temp_folder, f"{frame_number}.png")
            cv2.imwrite(frame_path, frame)

            try:
                clear_message = lsb.reveal(frame_path)
                if clear_message:
                    decoded_parts[frame_number] = clear_message
                    print(f"Frame {frame_number} decoded: {clear_message}")
                else:
                    print(f"No message found in frame {frame_number}")
            except Exception as e:
                print(f"Could not decode frame {frame_number}: {e}")

    cap.release()

    sorted_decoded_parts = [decoded_parts[f] for f in sorted(frames) if f in decoded_parts]
    encrypted_message = "".join(sorted_decoded_parts)

    if not encrypted_message:
        clean_tmp(temp_folder)
        return "Failed to recover any message parts from the specified frames."

    print(f"Full encrypted message: {encrypted_message}")

    if decryption_style == 'AES':
        if not key:
            raise ValueError("AES key is required for decryption.")
        decrypted_message = aesutil.decrypt(key=key, source=encrypted_message, keyType='ascii').decode('utf-8')
    elif decryption_style == 'RSA':
        if not rsa_key_path:
            raise ValueError("RSA private key path is required for decryption.")
        decrypted_message = rsautil1.decrypt(message=encrypted_message, key_path=rsa_key_path).decode('utf-8')
    else:
        raise ValueError("Invalid decryption style. Choose 'AES' or 'RSA'.")

    clean_tmp(temp_folder)
    return decrypted_message
