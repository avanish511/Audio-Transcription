import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
AWANLLM_API_KEY = os.getenv('AWANLLM_API_KEY')

upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
awanllm_endpoint = 'https://api.awanllm.com/v1/chat/completions'

def upload_audio(file):
    headers = {'Authorization': f'Bearer {ASSEMBLYAI_API_KEY}'}
    response = requests.post(upload_endpoint, headers=headers, files={'file': file})
    return response.json()['upload_url']

def request_transcription(audio_url):
    headers = {'Authorization': f'Bearer {ASSEMBLYAI_API_KEY}'}
    data = {
        'audio_url': audio_url,
        'speaker_labels': True
    }
    response = requests.post(transcript_endpoint, headers=headers, json=data)
    return response.json()['id']

def get_transcription_result(transcription_id):
    headers = {'Authorization': f'Bearer {ASSEMBLYAI_API_KEY}'}
    polling_endpoint = f'{transcript_endpoint}/{transcription_id}'
    while True:
        response = requests.get(polling_endpoint, headers=headers)
        result = response.json()
        if result['status'] == 'completed':
            return result
        elif result['status'] == 'failed':
            return None

def generate_response(transcription_text):
    headers = {'Authorization': f'Bearer {AWANLLM_API_KEY}', 'Content-Type': 'application/json'}
    data = {
        "model": "Awanllm-Llama-3-8B-Dolfin",
        "messages": [{"role": "user", "content": transcription_text}],
    }
    response = requests.post(awanllm_endpoint, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def display_transcription(transcription_result, time_range_seconds):
    st.write("### Transcription")
    segment_text = ""
    start_time_segment = 0

    for word in transcription_result['words']:
        start_time = word['start'] / 1000.0
        end_time = word['end'] / 1000.0

        if end_time - start_time_segment <= time_range_seconds:
            segment_text += f"{word['text']} "
        else:
            st.write(f"{start_time_segment:.2f}s - {end_time:.2f}s: {segment_text.strip()}")
            segment_text = f"{word['text']} "
            start_time_segment = end_time

    if segment_text:
        st.write(f"{start_time_segment:.2f}s - {end_time:.2f}s: {segment_text.strip()}")

def main():
    st.title("Audio Transcription with Speaker Diarization and AI Response")
    uploaded_file = st.file_uploader("Choose an audio file...", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/mp3')

        time_range_option = st.selectbox(
            "Select time range for displaying transcription:",
            ["1 second", "5 seconds", "10 seconds", "30 seconds", "Custom"], index=2
        )
        time_range_seconds = int(time_range_option.split()[0]) if time_range_option != "Custom" else st.number_input("Enter custom time range in seconds:", min_value=1, step=1)

        if st.button("Upload and Transcribe"):
            audio_url = upload_audio(uploaded_file)
            transcription_id = request_transcription(audio_url)
            transcription_result = get_transcription_result(transcription_id)
            if transcription_result:
                st.session_state['transcription_result'] = transcription_result
                st.session_state['time_range_seconds'] = time_range_seconds

        if 'transcription_result' in st.session_state:
            display_transcription(st.session_state['transcription_result'], st.session_state['time_range_seconds'])

        user_query = st.text_input("Ask a question based on the transcription:")
        if user_query:
            if st.button("Get AI Response"):
                response = generate_response(user_query)
                st.write("### AI Response")
                st.write(response)

if __name__ == "__main__":
    main()
