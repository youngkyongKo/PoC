"""
Text-to-Speech (음성 합성)
텍스트를 음성으로 변환
"""
import sys
from pathlib import Path
import logging
from typing import Optional
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class TextToSpeech:
    """음성 합성 클래스"""

    def __init__(self, language: str = None):
        """
        Args:
            language: TTS 언어 코드 (예: 'ko', 'en')
        """
        self.language = language or config.TTS_LANGUAGE
        logger.info(f"TextToSpeech initialized (language: {self.language})")

    def synthesize(
        self,
        text: str,
        output_file: str = None,
        slow: bool = False
    ) -> str:
        """
        텍스트를 음성으로 변환

        Args:
            text: 변환할 텍스트
            output_file: 출력 파일 경로 (None이면 임시 파일)
            slow: 느린 속도로 읽기

        Returns:
            오디오 파일 경로
        """
        try:
            from gtts import gTTS

            # Create temporary file if no output specified
            if output_file is None:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp3"
                ) as tmp_file:
                    output_file = tmp_file.name

            logger.info(f"Synthesizing text: '{text[:50]}...'")

            # Create TTS
            tts = gTTS(
                text=text,
                lang=self.language,
                slow=slow
            )

            # Save to file
            tts.save(output_file)

            logger.info(f"Audio saved to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return None

    def play(self, audio_file: str):
        """
        오디오 파일 재생

        Args:
            audio_file: 재생할 오디오 파일
        """
        try:
            from pydub import AudioSegment
            from pydub.playback import play

            logger.info(f"Playing audio: {audio_file}")

            # Load and play audio
            audio = AudioSegment.from_file(audio_file)
            play(audio)

            logger.info("Playback completed")

        except Exception as e:
            logger.error(f"Audio playback failed: {e}")

    def synthesize_and_play(
        self,
        text: str,
        slow: bool = False
    ):
        """
        텍스트를 음성으로 변환하고 재생

        Args:
            text: 변환할 텍스트
            slow: 느린 속도로 읽기
        """
        audio_file = self.synthesize(text, slow=slow)

        if audio_file:
            self.play(audio_file)

            # Clean up temporary file
            try:
                Path(audio_file).unlink()
            except:
                pass


def main():
    """테스트 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Text-to-Speech test")
    parser.add_argument(
        "text",
        help="Text to synthesize"
    )
    parser.add_argument(
        "--output",
        help="Output audio file"
    )
    parser.add_argument(
        "--language",
        default="ko",
        help="TTS language"
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Speak slowly"
    )
    parser.add_argument(
        "--play",
        action="store_true",
        help="Play audio after synthesis"
    )

    args = parser.parse_args()

    tts = TextToSpeech(language=args.language)

    if args.play:
        # Synthesize and play
        tts.synthesize_and_play(args.text, slow=args.slow)
    else:
        # Just synthesize
        output = args.output or "output.mp3"
        audio_file = tts.synthesize(args.text, output_file=output, slow=args.slow)
        print(f"\n✓ Audio saved to: {audio_file}")


if __name__ == "__main__":
    main()
