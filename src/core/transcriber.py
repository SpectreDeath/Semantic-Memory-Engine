"""
The Echo: Local Transcription Engine
GPU-accelerated Whisper transcription on 1660 Ti.
Converts YouTube URLs and audio files to text for Loom processing.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
from typing import Dict, Any
from datetime import datetime
import subprocess
import tempfile
import shutil

mcp = FastMCP("TranscriptionEcho")

STORAGE_DIR = os.path.normpath("D:/mcp_servers/storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")

# Create transcripts directory if needed
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

class WhisperTranscriber:
    """GPU-accelerated Whisper transcription."""
    
    def __init__(self, model_size: str = "medium"):
        """
        Initialize Whisper transcriber.
        model_size: 'tiny', 'base', 'small', 'medium', 'large'
        Medium = good balance of speed/quality for 1660 Ti
        """
        self.model_size = model_size
        self.device = "cuda"  # GPU mode for 1660 Ti
    
    def check_whisper_installed(self) -> bool:
        """Checks if OpenAI Whisper is installed."""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    def check_yt_dlp_installed(self) -> bool:
        """Checks if yt-dlp is installed."""
        try:
            import yt_dlp
            return True
        except ImportError:
            return False
    
    def download_youtube_audio(self, url: str) -> Dict[str, Any]:
        """Downloads audio from YouTube URL."""
        try:
            if not self.check_yt_dlp_installed():
                return {
                    'status': 'error',
                    'error': 'yt-dlp not installed. Run: pip install yt-dlp'
                }
            
            import yt_dlp
            
            # Create temporary file for audio
            temp_file = os.path.join(TRANSCRIPTS_DIR, f"temp_{datetime.now().timestamp()}.mp3")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': temp_file.replace('.mp3', ''),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', 'unknown')
            
            # Rename to final location
            downloaded_file = temp_file.replace('.mp3', '.mp3')
            
            return {
                'status': 'success',
                'audio_file': downloaded_file,
                'video_title': video_title,
                'url': url
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'note': 'Make sure FFmpeg is installed: https://ffmpeg.org/download.html'
            }
    
    def transcribe_audio(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """Transcribes audio file using Whisper."""
        try:
            if not self.check_whisper_installed():
                return {
                    'status': 'error',
                    'error': 'OpenAI Whisper not installed. Run: pip install openai-whisper'
                }
            
            if not os.path.exists(audio_path):
                return {'status': 'error', 'error': f'Audio file not found: {audio_path}'}
            
            import whisper
            
            # Load model (first run will download)
            model = whisper.load_model(self.model_size, device=self.device)
            
            # Transcribe
            result = model.transcribe(audio_path, language=language)
            
            return {
                'status': 'success',
                'text': result['text'],
                'language': result.get('language', language),
                'segments': len(result.get('segments', [])),
                'model': self.model_size,
                'device': self.device
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def transcribe_youtube(self, url: str) -> Dict[str, Any]:
        """End-to-end YouTube → transcript."""
        try:
            # Step 1: Download audio
            download_result = self.download_youtube_audio(url)
            
            if download_result['status'] == 'error':
                return download_result
            
            audio_file = download_result['audio_file']
            video_title = download_result.get('video_title', 'unknown')
            
            # Step 2: Transcribe
            transcribe_result = self.transcribe_audio(audio_file)
            
            if transcribe_result['status'] == 'error':
                return transcribe_result
            
            # Step 3: Save transcript
            transcript_data = {
                'timestamp': datetime.now().isoformat(),
                'source_url': url,
                'video_title': video_title,
                'text': transcribe_result['text'],
                'language': transcribe_result.get('language'),
                'model_used': self.model_size,
                'transcription_status': 'complete'
            }
            
            # Save to file
            transcript_file = os.path.join(
                TRANSCRIPTS_DIR,
                f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            # Clean up audio file
            try:
                os.remove(audio_file)
            except:
                pass
            
            return {
                'status': 'complete',
                'video_title': video_title,
                'transcript_file': transcript_file,
                'text_length': len(transcribe_result['text']),
                'word_count': len(transcribe_result['text'].split()),
                'ready_for_distillation': True,
                'transcript': transcribe_result['text'][:500] + "..." if len(transcribe_result['text']) > 500 else transcribe_result['text']
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


@mcp.tool()
def transcribe_youtube_url(url: str, model_size: str = "medium") -> str:
    """
    Transcribes YouTube video to text using Whisper.
    model_size: 'tiny'(fast), 'base', 'small', 'medium'(recommended), 'large'(slow)
    Returns transcript ready for Loom distillation.
    """
    try:
        transcriber = WhisperTranscriber(model_size)
        
        # Check dependencies
        if not transcriber.check_whisper_installed():
            return json.dumps({
                'status': 'error',
                'error': 'OpenAI Whisper not installed',
                'install': 'pip install openai-whisper'
            })
        
        if not transcriber.check_yt_dlp_installed():
            return json.dumps({
                'status': 'error',
                'error': 'yt-dlp not installed',
                'install': 'pip install yt-dlp'
            })
        
        # Transcribe
        result = transcriber.transcribe_youtube(url)
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def transcribe_audio_file(file_path: str, model_size: str = "medium") -> str:
    """
    Transcribes a local audio file using Whisper.
    Supports: MP3, WAV, M4A, FLAC, OGG, etc.
    """
    try:
        transcriber = WhisperTranscriber(model_size)
        
        if not transcriber.check_whisper_installed():
            return json.dumps({
                'status': 'error',
                'error': 'OpenAI Whisper not installed',
                'install': 'pip install openai-whisper'
            })
        
        if not os.path.exists(file_path):
            return json.dumps({
                'status': 'error',
                'error': f'File not found: {file_path}'
            })
        
        result = transcriber.transcribe_audio(file_path)
        
        # Save if successful
        if result['status'] == 'success':
            transcript_file = os.path.join(
                TRANSCRIPTS_DIR,
                f"transcript_{os.path.basename(file_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            transcript_data = {
                'timestamp': datetime.now().isoformat(),
                'source_file': file_path,
                'text': result['text'],
                'language': result.get('language'),
                'model_used': model_size,
                'word_count': len(result['text'].split())
            }
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            result['transcript_file'] = transcript_file
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def check_transcription_dependencies() -> str:
    """Checks if Whisper and yt-dlp are installed."""
    transcriber = WhisperTranscriber()
    
    dependencies = {
        'whisper': {
            'installed': transcriber.check_whisper_installed(),
            'install_command': 'pip install openai-whisper'
        },
        'yt-dlp': {
            'installed': transcriber.check_yt_dlp_installed(),
            'install_command': 'pip install yt-dlp'
        },
        'ffmpeg': {
            'note': 'Required by yt-dlp. Download from https://ffmpeg.org/download.html'
        }
    }
    
    all_ready = dependencies['whisper']['installed'] and dependencies['yt-dlp']['installed']
    
    return json.dumps({
        'dependencies': dependencies,
        'ready': all_ready,
        'status': 'ready' if all_ready else 'missing_dependencies'
    }, indent=2)


@mcp.tool()
def list_transcripts() -> str:
    """Lists all transcripts in storage."""
    try:
        transcripts = []
        
        if os.path.exists(TRANSCRIPTS_DIR):
            for file in os.listdir(TRANSCRIPTS_DIR):
                if file.endswith('.json') and file.startswith('transcript_'):
                    file_path = os.path.join(TRANSCRIPTS_DIR, file)
                    file_size = os.path.getsize(file_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        transcripts.append({
                            'filename': file,
                            'size_kb': round(file_size / 1024, 2),
                            'word_count': data.get('word_count', 0),
                            'source': data.get('source_url') or data.get('source_file'),
                            'timestamp': data.get('timestamp')
                        })
                    except:
                        pass
        
        return json.dumps({
            'transcript_count': len(transcripts),
            'transcripts': transcripts,
            'directory': TRANSCRIPTS_DIR
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_transcript_text(filename: str) -> str:
    """Retrieves full transcript text from file."""
    try:
        file_path = os.path.join(TRANSCRIPTS_DIR, filename)
        
        if not os.path.exists(file_path):
            return json.dumps({'error': f'Transcript not found: {filename}'})
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return json.dumps({
            'source': data.get('source_url') or data.get('source_file'),
            'title': data.get('video_title'),
            'text': data.get('text'),
            'word_count': len(data.get('text', '').split()),
            'ready_for_distillation': True
        }, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
