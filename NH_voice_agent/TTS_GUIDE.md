# Edge TTS 설정 가이드

Microsoft Edge TTS를 사용하여 **무료**로 **고품질** 한국어 음성을 사용합니다!

## 특징

✅ **완전 무료** - 인증이나 API 키 불필요
✅ **고품질** - Neural TTS (자연스러운 음성)
✅ **속도 조절** - 20% 빠르게 또는 느리게
✅ **피치 조절** - 음 높이 조절 가능
✅ **다양한 음성** - 5+ 한국어 음성 선택 가능

## 설치

```bash
pip install edge-tts
```

## 사용 가능한 한국어 음성

### 여성 음성 (추천)

1. **ko-KR-SunHiNeural** ⭐ (현재 설정)
   - 밝고 경쾌한 여성 음성
   - 친근하고 활발한 톤
   - 고객 서비스에 적합

2. **ko-KR-JiMinNeural**
   - 부드럽고 차분한 여성 음성
   - 안정적이고 온화한 톤

3. **ko-KR-SeoHyeonNeural**
   - 차분하고 전문적인 여성 음성
   - 공식적인 안내에 적합

### 남성 음성

1. **ko-KR-InJoonNeural**
   - 안정적이고 명확한 남성 음성
   - 중저음의 차분한 톤

2. **ko-KR-BongJinNeural**
   - 진중하고 권위있는 남성 음성
   - 공식 발표나 안내에 적합

3. **ko-KR-GookMinNeural**
   - 또 다른 남성 음성 옵션

4. **ko-KR-HyunsuNeural**
   - 젊고 활기찬 남성 음성

## 음성 설정 (.env 파일)

```bash
# 음성 선택
TTS_VOICE_NAME=ko-KR-SunHiNeural

# 말하기 속도
# +50% = 50% 빠르게, -20% = 20% 느리게
TTS_SPEAKING_RATE=+20%

# 피치 (음 높이)
# +10Hz = 약간 높게, -5Hz = 약간 낮게
TTS_PITCH=+5Hz
```

## 음성 테스트

### 모든 한국어 음성 듣기

```bash
cd 3_voice_app
python tts.py --list-voices
```

### 특정 음성으로 테스트

```bash
# 기본 음성 (SunHiNeural)
python tts.py "안녕하세요, NH증권입니다" --play

# 다른 음성 테스트
python tts.py "안녕하세요" --voice ko-KR-JiMinNeural --play

# 파일로 저장
python tts.py "테스트 메시지" --output test.mp3
```

## 음성 변경하기

`.env` 파일에서 `TTS_VOICE_NAME` 값을 변경하면 됩니다:

```bash
# 부드러운 여성 음성으로 변경
TTS_VOICE_NAME=ko-KR-JiMinNeural

# 남성 음성으로 변경
TTS_VOICE_NAME=ko-KR-InJoonNeural
```

앱을 재시작하면 새 음성이 적용됩니다.

## 추천 설정

### 밝고 경쾌한 여성 (현재 설정)
```bash
TTS_VOICE_NAME=ko-KR-SunHiNeural
TTS_SPEAKING_RATE=+20%
TTS_PITCH=+5Hz
```

### 부드러운 여성
```bash
TTS_VOICE_NAME=ko-KR-JiMinNeural
TTS_SPEAKING_RATE=+10%
TTS_PITCH=0Hz
```

### 안정적인 남성
```bash
TTS_VOICE_NAME=ko-KR-InJoonNeural
TTS_SPEAKING_RATE=+10%
TTS_PITCH=-3Hz
```

## 문제 해결

### RuntimeError: Event loop is closed
→ 정상 작동합니다. 내부적으로 비동기 처리 후 정리되는 경고입니다.

### edge_tts 모듈 없음
```bash
pip install edge-tts
```

### 음성이 너무 빠르거나 느림
`.env` 파일에서 `TTS_SPEAKING_RATE` 값을 조정하세요:
- 빠르게: `+30%` ~ `+50%`
- 보통: `0%` ~ `+10%`
- 느리게: `-20%` ~ `-10%`

## 비교: Edge TTS vs gTTS

| 항목 | Edge TTS | gTTS |
|------|----------|------|
| 비용 | 무료 | 무료 |
| 인증 | 불필요 | 불필요 |
| 품질 | Neural (매우 자연스러움) | 기본 (기계적) |
| 음성 선택 | 5+ 옵션 | 없음 |
| 속도 조절 | 세밀 조절 가능 | 느림/보통만 |
| 피치 조절 | 가능 | 불가능 |
| 추천 | ⭐⭐⭐⭐⭐ | ⭐⭐ |

## 결론

Edge TTS는 무료이면서도 Google Cloud TTS 수준의 품질을 제공합니다.
NH Voice Agent는 기본적으로 Edge TTS를 사용하도록 설정되어 있습니다.
