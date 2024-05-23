import os
import requests
import time
import streamlit as st
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')

upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'

assemblyai_headers = {
    'authorization': ASSEMBLYAI_API_KEY
}

def upload_audio(file):
    response = requests.post(upload_endpoint, headers=assemblyai_headers, files={'file': file})
    response_data = response.json()
    return response_data['upload_url']

def request_transcription(audio_url):
    data = {
        'audio_url': audio_url,
        'speaker_labels': True
    }
    response = requests.post(transcript_endpoint, json=data, headers=assemblyai_headers)
    response_data = response.json()
    return response_data['id']

def get_transcription_result(transcription_id):
    polling_endpoint = f'{transcript_endpoint}/{transcription_id}'
    while True:
        response = requests.get(polling_endpoint, headers=assemblyai_headers)
        response_data = response.json()
        if response_data['status'] == 'completed':
            return response_data
        elif response_data['status'] == 'failed':
            st.error('Transcription failed')
            return None
        time.sleep(10)

def display_transcription(transcription_result, time_range_seconds):
    st.write("### Transcription")
    start_time_segment = 0
    segment_text = ""

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
    st.title("Audio Transcription with Speaker Diarization and Timestamps")
    st.write("Upload an audio file and get the transcription with speaker diarization and timestamps.")

    uploaded_file = st.file_uploader("Choose an audio file...", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/mp3')

        time_range_option = st.selectbox(
            "Select time range for displaying transcription:", 
            ["1 second", "5 seconds", "10 seconds", "30 seconds", "Custom"],
            index=2
        )
        
        if time_range_option == "Custom":
            time_range_seconds = st.number_input("Enter custom time range in seconds:", min_value=1, step=1)
        else:
            time_range_seconds = int(time_range_option.split()[0])

        if st.button("Transcribe"):
            with st.spinner('Uploading audio...'):
                audio_url = upload_audio(uploaded_file)
                st.success('Audio uploaded successfully')

            with st.spinner('Requesting transcription...'):
                transcription_id = request_transcription(audio_url)
                st.success('Transcription requested successfully')

            with st.spinner('Waiting for transcription to complete...'):
                transcription_result = get_transcription_result(transcription_id)

            if transcription_result:
                st.success('Transcription completed successfully')
                st.session_state['transcription'] = transcription_result  # Store transcription in session state

        if 'transcription' in st.session_state:
            transcription_result = st.session_state['transcription']
            display_transcription(transcription_result, time_range_seconds)

if __name__ == "__main__":
    main()
