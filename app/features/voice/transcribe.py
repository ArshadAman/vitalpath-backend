import os
import logging
from pydub import AudioSegment
import requests

logger = logging.getLogger(__name__)

WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:9000")

def transcribe_audio_whisper(file_path: str, language: str = "hi") -> str:
    """
    Converts audio to WAV, sends to local Whisper ASR container,
    returns clean transcript text.
    
    Args:
        file_path: Path to audio file (M4A, WAV, MP3, etc.)
        language: Language code - 'hi' for Hinglish/Hindi, 'en' for English
    Returns:
        Transcribed text string
    """
    try:
        # Convert to WAV for best Whisper compatibility
        audio = AudioSegment.from_file(file_path)
        wav_path = file_path.rsplit(".", 1)[0] + ".wav"
        audio.export(wav_path, format="wav")
        logger.info(f"Converted audio to WAV: {wav_path} (duration: {len(audio)}ms)")

        # Build request params
        params = {
            "encode": "true",
            "task": "transcribe",
            "language": language,
            "output": "json",
        }
        
        # For Hinglish, add an initial prompt to bias the decoder
        if language == "hi":
            params["initial_prompt"] = (
                "Yeh ek health journal hai. Maine aaj exercise kiya aur paani piya. "
                "Doctor ne kaha ki meri health improve ho rahi hai."
            )

        # Call local Whisper REST API
        with open(wav_path, "rb") as f:
            response = requests.post(
                f"{WHISPER_URL}/asr",
                params=params,
                files={"audio_file": ("audio.wav", f, "audio/wav")},
                timeout=120,  # 2 min timeout for longer recordings
            )
        
        response.raise_for_status()
        result = response.json()
        transcript = result.get("text", "").strip()
        
        logger.info(f"Whisper transcription complete: {transcript[:100]}...")
        
        # Cleanup temp WAV file
        if os.path.exists(wav_path):
            os.remove(wav_path)
            
        return transcript
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Whisper ASR container. Is it running?")
        raise RuntimeError("Whisper ASR service unavailable")
    except Exception as e:
        logger.exception(f"Transcription failed: {e}")
        raise
