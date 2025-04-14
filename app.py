import streamlit as st
import assemblyai as aai
import time
import os
import threading
from st_copy_to_clipboard import st_copy_to_clipboard as clipboard

# --- Configuration ---
def get_estimated_time(file_path):
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return max(5, file_size_mb * 6)  # 1MB = 6s, min 5s

# --- Background transcription ---
def transcribe_audio(file_path, result_dict, transcriber):
    result_dict["start_time"] = time.time()
    try:
        transcript = transcriber.transcribe(file_path)
        result_dict["text"] = transcript.text
    except Exception as e:
        result_dict["text"] = f"Error: {e}"
    result_dict["end_time"] = time.time()
    result_dict["done"] = True

# --- UI progress handler ---
def show_progress(estimated_time, result_dict, status_placeholder, progress_bar):
    for i in range(int(estimated_time), 0, -1):
        if result_dict["done"]:
            break
        status_placeholder.text(f"Transcribing... {i} seconds left")
        progress_bar.progress((estimated_time - i) / estimated_time)
        time.sleep(1)
    status_placeholder.text("Finalizing transcription...")

# --- Main app logic ---
def main():
    st.title("GA Audio Transcriber")
    
    with st.expander(" **🧭 How to Use This App?**"):
        st.markdown("""
            1. **Get Your API Key**  
                - Go to [https://www.assemblyai.com](https://www.assemblyai.com)  
                - Sign up or log in  
                - Copy your API Key from the dashboard

            2. **Paste the API Key in the Field Above**

            3. **Upload a Voice Note**  
                - Supported formats: MP3, WAV, AAC, FLAC, M4A, OGG, WEBM

            4. **Click "Start Transcription"**  
                - Wait for the process to finish  
                - View your transcribed text below

            5. **Click "📋 Copy to Clipboard" and Paste to CHATGPT to summarize the text**
            """)

    api_key = st.text_input("Enter API Key:")

    if not api_key:
        return

    aai.settings.api_key = api_key
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.nano, language_detection=True)
    transcriber = aai.Transcriber(config=config)

    audio_file = st.file_uploader("Upload audio file", type=['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg', 'webm'])
    st.audio(audio_file)

    if st.button("Start Transcription"):
        if not audio_file:
            st.warning("Please upload an audio file.")
            return

        # Save file
        temp_path = "temp_audio"
        with open(temp_path, "wb") as f:
            f.write(audio_file.read())

        # Setup
        estimated_time = get_estimated_time(temp_path)
        st.info(f"Estimated Transcription Time: {round(estimated_time)} seconds")
        status = st.empty()
        progress = st.progress(0)

        result = {"text": "", "done": False, "start_time": None, "end_time": None}

        # Start transcription in thread
        thread = threading.Thread(target=transcribe_audio, args=(temp_path, result, transcriber))
        thread.start()

        # Show progress while thread is running
        show_progress(estimated_time, result, status, progress)
        thread.join()

        # Show result
        progress.progress(1.0)
        if result["text"].startswith("Error"):
            st.error(result["text"])
        else:
            duration = round(result["end_time"] - result["start_time"], 2)
            st.success(f"Transcription completed in {duration} seconds")
            st.text_area("Transcription Output", result["text"], height=300)

            text_prompt = "Tolong kemaskan dan susun semula transkrip perbualan ini supaya menjadi ayat yang tersusun, mudah difahami, dan sesuai dibaca oleh staf pengurusan. Kekalkan maksud asal. Gunakan Bahasa Melayu. Jika ada bahagian yang tidak jelas, simpulkan sahaja secara logik. Ini transkripnya: "

            clipboard(text_prompt + result["text"], before_copy_label="📋 Copy to Clipboard")

if __name__ == "__main__":
    main()
