"""
Speech-to-Text (음성 인식)
마이크 입력을 텍스트로 변환
"""
import sys
from pathlib import Path
import logging
from typing import Optional
import tempfile

from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class SpeechToText:
    """음성 인식 클래스"""

    def __init__(self, language: str = None):
        """
        Args:
            language: 인식 언어 코드 (예: 'ko-KR', 'en-US')
        """
        self.language = language or config.SPEECH_LANGUAGE

        # Method 선택: whisper 또는 google
        self.method = "google"  # 'whisper' or 'google'

        logger.info(f"SpeechToText initialized (method: {self.method}, language: {self.language})")

    def recognize_from_file(self, audio_file: str) -> Optional[str]:
        """
        오디오 파일에서 텍스트 인식

        Args:
            audio_file: 오디오 파일 경로

        Returns:
            인식된 텍스트
        """
        try:
            if self.method == "whisper":
                return self._recognize_whisper(audio_file)
            else:
                return self._recognize_google(audio_file)

        except Exception as e:
            logger.error(f"Error recognizing speech: {e}")
            return None

    def _recognize_whisper(self, audio_file: str) -> Optional[str]:
        """
        Whisper 모델로 음성 인식

        Args:
            audio_file: 오디오 파일 경로

        Returns:
            인식된 텍스트
        """
        try:
            import whisper

            # Load model
            model = whisper.load_model("base")

            # Transcribe
            result = model.transcribe(
                audio_file,
                language="ko" if self.language.startswith("ko") else "en"
            )

            text = result["text"].strip()
            logger.info(f"Whisper recognized: '{text}'")

            return text

        except Exception as e:
            logger.error(f"Whisper recognition failed: {e}")
            return None

    def _recognize_google(self, audio_file: str) -> Optional[str]:
        """
        Google Speech Recognition으로 음성 인식

        Args:
            audio_file: 오디오 파일 경로

        Returns:
            인식된 텍스트
        """
        import os
        import tempfile

        try:
            import speech_recognition as sr
            from pydub import AudioSegment

            logger.info(f"Processing audio file: {audio_file}")

            # Check file exists and size
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                return None

            file_size = os.path.getsize(audio_file)
            logger.info(f"Audio file size: {file_size} bytes")

            if file_size < 100:  # Too small
                logger.error("Audio file too small")
                return None

            # Convert to WAV format using pydub
            # This handles WebM, OGG, and other formats
            try:
                logger.info("Converting audio to WAV format...")
                audio_segment = AudioSegment.from_file(audio_file)

                # Export as WAV
                wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                wav_path = wav_file.name
                wav_file.close()

                audio_segment.export(
                    wav_path,
                    format="wav",
                    parameters=["-ar", "16000", "-ac", "1"]  # 16kHz, mono
                )

                logger.info(f"Converted to WAV: {wav_path}")

            except Exception as conv_error:
                logger.error(f"Audio conversion failed: {conv_error}")
                # Try to use original file
                wav_path = audio_file

            # Speech recognition
            recognizer = sr.Recognizer()

            # Adjust for ambient noise and energy threshold
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            # Load audio file
            try:
                with sr.AudioFile(wav_path) as source:
                    # Adjust for ambient noise
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)

                    # Record audio
                    audio = recognizer.record(source)

                    logger.info(f"Audio recorded, duration: ~{len(audio.frame_data) / (audio.sample_rate * audio.sample_width)} seconds")

            except Exception as read_error:
                logger.error(f"Failed to read audio file: {read_error}")
                # Clean up temp file
                if wav_path != audio_file and os.path.exists(wav_path):
                    os.unlink(wav_path)
                return None

            # Recognize with timeout
            try:
                logger.info("Calling Google Speech Recognition API...")
                text = recognizer.recognize_google(
                    audio,
                    language=self.language
                )

                logger.info(f"Google STT recognized: '{text}'")

                # Clean up temp WAV file
                if wav_path != audio_file and os.path.exists(wav_path):
                    os.unlink(wav_path)

                return text

            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Google Speech Recognition service error: {e}")
                return None

        except Exception as e:
            logger.error(f"Google STT recognition failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def recognize_from_microphone(self, duration: int = 5) -> Optional[str]:
        """
        마이크에서 직접 음성 인식

        Args:
            duration: 녹음 시간 (초)

        Returns:
            인식된 텍스트
        """
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()

            with sr.Microphone() as source:
                logger.info(f"Recording for {duration} seconds...")
                print("🎤 말씀하세요...")

                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Record audio
                audio = recognizer.record(source, duration=duration)

                logger.info("Processing...")
                print("⏳ 처리 중...")

                # Recognize
                text = recognizer.recognize_google(
                    audio,
                    language=self.language
                )

                logger.info(f"Recognized: '{text}'")
                return text

        except Exception as e:
            logger.error(f"Microphone recognition failed: {e}")
            return None


def main():
    """테스트 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Speech-to-Text test")
    parser.add_argument(
        "--file",
        help="Audio file to transcribe"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Recording duration (seconds)"
    )
    parser.add_argument(
        "--language",
        default="ko-KR",
        help="Speech language"
    )

    args = parser.parse_args()

    stt = SpeechToText(language=args.language)

    if args.file:
        # Transcribe file
        print(f"Transcribing file: {args.file}")
        text = stt.recognize_from_file(args.file)
        print(f"\nRecognized text: {text}")
    else:
        # Record from microphone
        print(f"Recording from microphone for {args.duration} seconds...")
        text = stt.recognize_from_microphone(duration=args.duration)
        print(f"\nRecognized text: {text}")


if __name__ == "__main__":
    main()
