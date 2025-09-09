import json
import logging
import os
import threading
import time
import queue
import pyaudio
import vosk
import asyncio
from typing import Dict, Callable, Optional

class VoskSpeechRecognizer:
    def __init__(self, model_path: str, sample_rate: int = 16000, chunk_size: int = 4000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.model = None
        self.recognizer = None
        self.audio_stream = None
        self.is_recognizing = False
        self.audio_queue = queue.Queue()
        self.recognition_thread = None
        self.audio_thread = None
        
        # Callbacks for speech events
        self.on_recognizing_callback: Optional[Callable] = None
        self.on_recognized_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Vosk model"""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Vosk model not found at {self.model_path}")
            
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            logging.info(f"Vosk model loaded successfully from {self.model_path}")
        except Exception as e:
            logging.error(f"Failed to initialize Vosk model: {e}")
            raise
    
    def set_callbacks(self, on_recognizing: Callable = None, on_recognized: Callable = None, on_error: Callable = None):
        """Set callback functions for speech recognition events"""
        self.on_recognizing_callback = on_recognizing
        self.on_recognized_callback = on_recognized
        self.on_error_callback = on_error
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio input"""
        if self.is_recognizing:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def _recognition_worker(self):
        """Worker thread for processing audio and recognition"""
        while self.is_recognizing:
            try:
                # Get audio data from queue
                if not self.audio_queue.empty():
                    data = self.audio_queue.get()
                    
                    if self.recognizer.AcceptWaveform(data):
                        # Final result
                        result = json.loads(self.recognizer.Result())
                        if result.get('text'):
                            if self.on_recognized_callback:
                                self.on_recognized_callback(result['text'])
                    else:
                        # Partial result
                        result = json.loads(self.recognizer.PartialResult())
                        if result.get('partial'):
                            if self.on_recognizing_callback:
                                self.on_recognizing_callback(result['partial'])
                
                time.sleep(0.01)  # Small delay to prevent high CPU usage
                
            except Exception as e:
                logging.error(f"Error in recognition worker: {e}")
                if self.on_error_callback:
                    self.on_error_callback(str(e))
                break
    
    def start_recognition(self):
        """Start continuous speech recognition"""
        if self.is_recognizing:
            logging.warning("Recognition is already running")
            return
        
        try:
            # Initialize audio stream
            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recognizing = True
            
            # Start recognition thread
            self.recognition_thread = threading.Thread(target=self._recognition_worker, daemon=True)
            self.recognition_thread.start()
            
            # Start audio stream
            self.audio_stream.start_stream()
            
            logging.info("Vosk speech recognition started")
            
        except Exception as e:
            logging.error(f"Failed to start recognition: {e}")
            self.stop_recognition()
            raise
    
    def stop_recognition(self):
        """Stop speech recognition"""
        if not self.is_recognizing:
            return
        
        self.is_recognizing = False
        
        # Stop audio stream
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        # Terminate audio
        if hasattr(self, 'audio'):
            self.audio.terminate()
        
        # Wait for recognition thread to finish
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=1.0)
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        logging.info("Vosk speech recognition stopped")
    
    def get_final_result(self):
        """Get the final recognition result"""
        if self.recognizer:
            return json.loads(self.recognizer.FinalResult())
        return None
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_recognition()

