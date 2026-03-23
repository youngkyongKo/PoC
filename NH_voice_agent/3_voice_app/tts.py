"""
Text-to-Speech (음성 합성)
텍스트를 음성으로 변환 - Microsoft Edge TTS 사용
"""
import sys
from pathlib import Path
import logging
from typing import Optional
import tempfile
import asyncio

from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class TextToSpeech:
    """음성 합성 클래스 - Microsoft Edge TTS (Neural) 사용"""

    def __init__(self, language: str = None):
        """
        Args:
            language: TTS 언어 코드 (예: 'ko', 'en')
        """
        self.language = language or config.TTS_LANGUAGE
        self.voice_name = config.TTS_VOICE_NAME
        self.speaking_rate = config.TTS_SPEAKING_RATE
        self.pitch = config.TTS_PITCH

        logger.info(f"TextToSpeech initialized with Edge TTS")
        logger.info(f"Voice: {self.voice_name}, Rate: {self.speaking_rate}, Pitch: {self.pitch}")

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
            # Create temporary file if no output specified
            if output_file is None:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp3"
                ) as tmp_file:
                    output_file = tmp_file.name

            logger.info(f"Synthesizing text: '{text[:50]}...'")

            # Run async synthesis with proper event loop handling
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a new event loop in a new thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._synthesize_async(text, output_file, slow)
                        )
                        future.result(timeout=30)
                else:
                    asyncio.run(self._synthesize_async(text, output_file, slow))
            except RuntimeError:
                # No event loop exists, create one
                asyncio.run(self._synthesize_async(text, output_file, slow))

            logger.info(f"Audio saved to: {output_file} (Edge TTS)")
            return output_file

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _synthesize_async(
        self,
        text: str,
        output_file: str,
        slow: bool = False
    ):
        """
        비동기 음성 합성

        Args:
            text: 변환할 텍스트
            output_file: 출력 파일 경로
            slow: 느린 속도로 읽기
        """
        import edge_tts

        # Adjust speaking rate for slow mode
        rate = self.speaking_rate
        if slow:
            rate = "-20%"

        # Create TTS communicator
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice_name,
            rate=rate,
            pitch=self.pitch
        )

        # Save to file
        await communicate.save(output_file)

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

    @staticmethod
    async def list_voices():
        """
        사용 가능한 음성 목록 조회

        Returns:
            음성 목록
        """
        import edge_tts

        voices = await edge_tts.list_voices()

        # Filter Korean voices
        korean_voices = [v for v in voices if v["Locale"].startswith("ko")]

        return korean_voices


def main():
    """테스트 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Text-to-Speech test (Edge TTS)")
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to synthesize"
    )
    parser.add_argument(
        "--output",
        help="Output audio file"
    )
    parser.add_argument(
        "--voice",
        help="Voice name (e.g., ko-KR-SunHiNeural)"
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
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available Korean voices"
    )

    args = parser.parse_args()

    # List voices
    if args.list_voices:
        async def list_and_print():
            tts = TextToSpeech()
            voices = await tts.list_voices()
            print("\n사용 가능한 한국어 음성:")
            print("-" * 60)
            for v in voices:
                gender = "여성" if v["Gender"] == "Female" else "남성"
                print(f"{v['ShortName']:<30} ({gender}) - {v['FriendlyName']}")
            print("-" * 60)

        asyncio.run(list_and_print())
        return

    if not args.text:
        parser.print_help()
        return

    tts = TextToSpeech()

    # Override voice if specified
    if args.voice:
        tts.voice_name = args.voice

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
