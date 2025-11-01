import streamlit as st
from encode import encode_process
from decode import decode_process
import tempfile
import os
import time

st.set_page_config(page_title="Video Steganography", layout="wide")
st.title("🎥 Video Steganography")

tab1, tab2 = st.tabs(["Encode", "Decode"])

# ============================ ENCODE TAB ============================
with tab1:
    st.subheader("🔒 Encode Message into Video")

    video_file = st.file_uploader("Upload Video", type=["mp4", "avi", "mkv"])
    message = st.text_area("Message to Hide")
    encryption_style = st.radio("Encryption Style", ["AES", "RSA"])

    col1, col2 = st.columns(2)
    with col1:
        aes_key = st.text_input("AES Key (for AES encryption)", type="password")
    with col2:
        rsa_public_key = st.file_uploader("RSA Public Key (for RSA or AES key encryption)", type=["pem"])

    frame_storage_image = st.file_uploader("Optional: Image to Hide Frame Numbers", type=["png", "jpg", "jpeg"])

    if st.button("🚀 Encode Video"):
        if not video_file or not message:
            st.error("⚠️ Video and message are required.")
        else:
            try:
                with st.spinner("🔄 Preparing files..."):
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_video:
                        tmp_video.write(video_file.read())
                        video_path = tmp_video.name

                    key_path = None
                    if rsa_public_key:
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_key:
                            tmp_key.write(rsa_public_key.read())
                            key_path = tmp_key.name

                    frame_image_path = None
                    if frame_storage_image:
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_img:
                            tmp_img.write(frame_storage_image.read())
                            frame_image_path = tmp_img.name

                progress_bar = st.progress(0)
                for i in range(0, 100, 10):
                    time.sleep(0.05)  # simulate progress
                    progress_bar.progress(i)

                st.spinner("🔐 Encoding in progress...")
                result = encode_process(
                    video_path=video_path,
                    message=message,
                    encryption_style=encryption_style,
                    key=aes_key,
                    key_path=key_path,
                    frame_storage_image=frame_image_path
                )
                progress_bar.progress(100)

                output_video = result.get('video')
                output_image = result.get('image')
                encrypted_key = result.get('encrypted_aes_key', "No key generated.")

                if output_video and os.path.exists(output_video):
                    st.success("✅ Video encoded successfully!")
                    with open(output_video, "rb") as f:
                        st.download_button("⬇️ Download Encoded Video", f, file_name="encoded_video.mp4")
                else:
                    st.warning("⚠️ Encoded video not found in result.")

                st.text_area("🔐 AES Key (Encrypted with RSA)", encrypted_key)

                if output_image and os.path.exists(output_image):
                    st.image(output_image, caption="Image with Hidden Frame Numbers")

            except Exception as e:
                st.error(f"❌ Error during encoding: {str(e)}")


# ============================ DECODE TAB ============================
with tab2:
    st.subheader("🔓 Decode Message from Video")

    encoded_video = st.file_uploader("Upload Encoded Video", type=["mp4", "avi", "mkv"])
    decryption_style = st.radio("Decryption Style", ["AES", "RSA"])

    col3, col4 = st.columns(2)
    with col3:
        aes_key_dec = st.text_input("AES Key (for AES decryption)", type="password")
    with col4:
        rsa_private_key = st.file_uploader("RSA Private Key (for RSA decryption)", type=["pem"])

    st.markdown("### Optional: Provide Frame Information")
    frame_option = st.radio("Choose frame input method", ["From Image", "Manual Entry"])

    encoded_image = None
    frames_manual = None

    if frame_option == "From Image":
        encoded_image = st.file_uploader("Image with Hidden Frame Numbers", type=["png", "jpg", "jpeg"])
    else:
        frames_manual = st.text_input("Comma-separated frame numbers (e.g., 10,20,30)")

    if st.button("🧩 Decode Video"):
        if not encoded_video:
            st.error("⚠️ Encoded video is required.")
        else:
            try:
                with st.spinner("🔄 Preparing files..."):
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_vid:
                        tmp_vid.write(encoded_video.read())
                        video_path = tmp_vid.name

                    rsa_key_path = None
                    if rsa_private_key:
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_key:
                            tmp_key.write(rsa_private_key.read())
                            rsa_key_path = tmp_key.name

                    image_path = None
                    if encoded_image:
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_img:
                            tmp_img.write(encoded_image.read())
                            image_path = tmp_img.name

                progress_bar = st.progress(0)
                for i in range(0, 100, 10):
                    time.sleep(0.05)  # simulate progress
                    progress_bar.progress(i)

                st.spinner("🔓 Decoding in progress...")
                decrypted_message = decode_process(
                    encoded_video_path=video_path,
                    decryption_style=decryption_style,
                    encoded_image_path=image_path,
                    frames_input=frames_manual,
                    key=aes_key_dec,
                    rsa_key_path=rsa_key_path
                )
                progress_bar.progress(100)

                st.success("✅ Message Decoded Successfully!")
                st.text_area("💬 Decoded Message", decrypted_message)

            except Exception as e:
                st.error(f"❌ Error during decoding: {str(e)}")
