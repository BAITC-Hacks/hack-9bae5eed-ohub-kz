# Alem Protocol

Track 08 Innovacii Samruk-Kazyna

## Run
docker-compose up --build
http://localhost:8000

## Test
curl -F "file=@meeting.mp3" http://localhost:8000/transcribe

## On-prem
STT local faster-whisper large-v3, diarization local pyannote, LLM local fallback + OpenAI optional.

## Codex used for stt, diarization, export modules
