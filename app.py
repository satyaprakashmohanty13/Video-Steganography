import gradio as gr
from encode import encode_process
from decode import decode_process
import os

def handle_encode(video, message, encryption_style, key, public_key_file, frame_storage_image):
    if not video or not message:
        return None, "Video and message are required.", None

    video_path = video.name
    key_path = public_key_file.name if public_key_file else None
    frame_image_path = frame_storage_image.name if frame_storage_image else None

    try:
        result = encode_process(
            video_path=video_path,
            message=message,
            encryption_style=encryption_style,
            key=key,
            key_path=key_path,
            frame_storage_image=frame_image_path
        )

        output_video = result.get('video')
        output_image = result.get('image')
        encrypted_key = result.get('encrypted_aes_key', "No key generated.")

        return output_video, f"AES Key (Encrypted with RSA): {encrypted_key}", output_image

    except Exception as e:
        return None, str(e), None

def handle_decode(encoded_video, decryption_style, encoded_image, frames_input, key, private_key_file):
    if not encoded_video:
        return "Encoded video is required."

    video_path = encoded_video.name
    image_path = encoded_image.name if encoded_image else None
    rsa_key_path = private_key_file.name if private_key_file else None

    try:
        decrypted_message = decode_process(
            encoded_video_path=video_path,
            decryption_style=decryption_style,
            encoded_image_path=image_path,
            frames_input=frames_input,
            key=key,
            rsa_key_path=rsa_key_path
        )
        return decrypted_message
    except Exception as e:
        return f"Error during decoding: {str(e)}"

with gr.Blocks() as demo:
    gr.Markdown("# Video Steganography")

    with gr.Tab("Encode"):
        video_input = gr.File(label="Upload Video")
        message_input = gr.Textbox(label="Message to Hide")
        encryption_style_input = gr.Radio(["AES", "RSA"], label="Encryption Style")

        with gr.Row():
            aes_key_input = gr.Textbox(label="AES Key (for AES encryption)", type="password")
            rsa_public_key_input = gr.File(label="RSA Public Key (for RSA or to encrypt AES key)")

        frame_storage_input = gr.File(label="Optional: Image to Hide Frame Numbers")

        encode_button = gr.Button("Encode Video")

        encoded_video_output = gr.File(label="Encoded Video")
        status_output = gr.Textbox(label="Status & Encrypted AES Key")
        encoded_image_output = gr.Image(label="Image with Hidden Frame Numbers", type="filepath")

        encode_button.click(
            fn=handle_encode,
            inputs=[video_input, message_input, encryption_style_input, aes_key_input, rsa_public_key_input, frame_storage_input],
            outputs=[encoded_video_output, status_output, encoded_image_output]
        )

    with gr.Tab("Decode"):
        encoded_video_input_decode = gr.File(label="Upload Encoded Video")
        decryption_style_input_decode = gr.Radio(["AES", "RSA"], label="Decryption Style")

        with gr.Row():
            aes_key_input_decode = gr.Textbox(label="AES Key (for AES decryption)", type="password")
            rsa_private_key_input_decode = gr.File(label="RSA Private Key (for RSA decryption)")

        with gr.Tab("Frame Numbers from Image"):
            encoded_image_input_decode = gr.File(label="Image with Hidden Frame Numbers")
        with gr.Tab("Manual Frame Numbers"):
            frames_manual_input = gr.Textbox(label="Comma-separated frame numbers (e.g., 10,20,30)")

        decode_button = gr.Button("Decode Video")
        decoded_message_output = gr.Textbox(label="Decoded Message")

        decode_button.click(
            fn=handle_decode,
            inputs=[
                encoded_video_input_decode,
                decryption_style_input_decode,
                encoded_image_input_decode,
                frames_manual_input,
                aes_key_input_decode,
                rsa_private_key_input_decode
            ],
            outputs=decoded_message_output
        )

if __name__ == "__main__":
    demo.launch(share=True)
