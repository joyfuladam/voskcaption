from vosk_speech_recognizer import VoskSpeechRecognizer
import logging
import os
import asyncio
import threading
import socket
from fastapi import FastAPI, Depends, HTTPException, WebSocket, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import time
import atexit
from threading import Timer
import unittest
import schedule
import json
from datetime import datetime, date
import re
import sounddevice as sd
import textwrap
from dotenv import load_dotenv
import webbrowser

# Load environment variables from .env file
load_dotenv()

# -------------------------------------------------------------------
# Setup logging
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Check if Vosk model exists
VOSK_MODEL_PATH = os.path.join(CURRENT_DIR, "models", "vosk-model-en-us-0.22")
if not os.path.exists(VOSK_MODEL_PATH):
    print("⚠️  Vosk model not found. Please run: python download_vosk_model.py")
    print(f"Expected model path: {VOSK_MODEL_PATH}")
LOG_FILE = os.path.join(CURRENT_DIR, "caption_log.txt")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [SpeechCaption] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_message(level, message):
    logging.log(level, f"[SpeechCaption] {message}")

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
CONFIG_FILE = os.path.join(CURRENT_DIR, "config.json")

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        # Override model_path with environment variable if set
        config["model_path"] = os.getenv("VOSK_MODEL_PATH", config.get("model_path", VOSK_MODEL_PATH))
        log_message(logging.INFO, "Configuration loaded successfully")
        return config
    except FileNotFoundError:
        log_message(logging.ERROR, f"Config file not found at {CONFIG_FILE}")
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    except json.JSONDecodeError as e:
        log_message(logging.ERROR, f"Failed to parse config JSON: {e}")
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to load config: {e}")
        raise

CONFIG = load_config()

# Validate Vosk model path
if not CONFIG.get("model_path") or not os.path.exists(CONFIG["model_path"]):
    raise ValueError(f"Vosk model not found at {CONFIG.get('model_path', 'not set')}. Please run: python download_vosk_model.py")

# -------------------------------------------------------------------
# File Paths
# -------------------------------------------------------------------
SCHEDULE_FILE = os.path.join(CURRENT_DIR, "schedule.json")
DICTIONARY_FILE = os.path.join(CURRENT_DIR, "dictionary.json")
USER_SETTINGS_FILE = os.path.join(CURRENT_DIR, "user_settings.json")

# Default user settings
DEFAULT_USER_SETTINGS = {
    "user_bg_color": "#000000",
    "user_text_color": "#FFFFFF",
    "user_font_style": "Arial",
    "user_font_size": 24,
    "user_max_line_length": 500,
    "user_lines": 3,
    "user_auto_finalize_delay": 10.0  # 10 seconds
}

# -------------------------------------------------------------------
# User Settings Persistence
# -------------------------------------------------------------------
def load_user_settings():
    try:
        if not os.path.exists(USER_SETTINGS_FILE):
            log_message(logging.WARNING, f"User settings file not found at {USER_SETTINGS_FILE}")
            return DEFAULT_USER_SETTINGS.copy()
        with open(USER_SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            log_message(logging.INFO, "User settings loaded successfully")
            return data
    except json.JSONDecodeError as e:
        log_message(logging.ERROR, f"Failed to parse user settings JSON: {e}")
        return DEFAULT_USER_SETTINGS.copy()
    except Exception as e:
        log_message(logging.ERROR, f"Failed to load user settings: {e}")
        return DEFAULT_USER_SETTINGS.copy()

def save_user_settings(settings):
    try:
        with open(USER_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        log_message(logging.INFO, "User settings saved")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to save user settings: {e}")

# Load initial user settings
USER_SETTINGS = load_user_settings()

# -------------------------------------------------------------------
# Load HTML templates at startup
# -------------------------------------------------------------------
def load_html_template(filename):
    try:
        with open(os.path.join(CURRENT_DIR, filename), 'r') as f:
            template = f.read()
        log_message(logging.INFO, f"Loaded HTML template: {filename}")
        return template
    except Exception as e:
        log_message(logging.ERROR, f"Failed to load HTML template {filename}: {e}")
        raise

ROOT_TEMPLATE = load_html_template("root.html")
USER_TEMPLATE = load_html_template("user.html")
SETUP_TEMPLATE = load_html_template("setup.html")
DICTIONARY_PAGE_TEMPLATE = load_html_template("dictionary_page.html")

# -------------------------------------------------------------------
# Dictionary Persistence
# -------------------------------------------------------------------
def load_dictionary():
    try:
        if not os.path.exists(DICTIONARY_FILE):
            log_message(logging.WARNING, f"Dictionary file not found at {DICTIONARY_FILE}")
            return {"bible_books": [], "spelling_corrections": {}, "custom_phrases": [], "supported_languages": []}
        with open(DICTIONARY_FILE, 'r') as f:
            data = json.load(f)
            log_message(logging.INFO, "Dictionary loaded successfully")
            return data
    except json.JSONDecodeError as e:
        log_message(logging.ERROR, f"Failed to parse dictionary JSON: {e}")
        return {"bible_books": [], "spelling_corrections": {}, "custom_phrases": [], "supported_languages": []}
    except Exception as e:
        log_message(logging.ERROR, f"Failed to load dictionary: {e}")
        return {"bible_books": [], "spelling_corrections": {}, "custom_phrases": [], "supported_languages": []}

def save_dictionary(dictionary):
    try:
        with open(DICTIONARY_FILE, 'w') as f:
            json.dump(dictionary, f, indent=2)
        log_message(logging.INFO, "Dictionary saved")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to save dictionary: {e}")

# -------------------------------------------------------------------
# Schedule Persistence
# -------------------------------------------------------------------
def load_schedule():
    try:
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    migrated_schedules = []
                    today = datetime.now().date()
                    for s in data:
                        if 'recurrence_type' not in s:
                            s['recurrence_type'] = 'yearly' if s.get('is_recurring', False) else 'one-time'
                            s.pop('is_recurring', None)
                        
                        # Handle different recurrence types
                        schedule_date = datetime.strptime(s['date'], '%Y-%m-%d').date()
                        if s['recurrence_type'] == 'one-time':
                            # Skip if the event is in the past
                            if schedule_date < today:
                                continue
                        elif s['recurrence_type'] == 'weekly':
                            # Keep if it's a weekly event (regardless of date)
                            pass
                        elif s['recurrence_type'] == 'monthly':
                            # Keep if it's a monthly event (regardless of date)
                            pass
                        elif s['recurrence_type'] == 'yearly':
                            # Keep if it's a yearly event (regardless of date)
                            pass
                        
                        migrated_schedules.append(s)
                    
                    # Save the cleaned schedule if any past events were removed
                    if len(migrated_schedules) < len(data):
                        save_schedule(migrated_schedules)
                        log_message(logging.INFO, "Cleaned up past events from schedule")
                    
                    return migrated_schedules
                if isinstance(data, dict) and (data.get('start_time') or data.get('stop_time')):
                    today = date.today().isoformat()
                    return [{
                        'date': today,
                        'start_time': data.get('start_time', ''),
                        'stop_time': data.get('stop_time', ''),
                        'recurrence_type': 'one-time'
                    }]
        return []
    except Exception as e:
        log_message(logging.ERROR, f"Failed to load schedule: {e}")
        return []

def save_schedule(schedules):
    try:
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)
        log_message(logging.INFO, f"Schedules saved: {len(schedules)} entries")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to save schedule: {e}")

# -------------------------------------------------------------------
# FastAPI Setup
# -------------------------------------------------------------------
app = FastAPI()
clients = []
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USERNAME", "admin")
    correct_password = os.getenv("ADMIN_PASSWORD", "Northway12121")
    log_message(logging.DEBUG, f"Auth attempt: provided username={credentials.username}")
    if not (credentials.username == correct_username and credentials.password == correct_password):
        log_message(logging.WARNING, f"Authentication failed for user: {credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

socket_ip = get_local_ip()
log_message(logging.INFO, f"WebSocket IP: {socket_ip}")

@app.get("/get_ip")
async def get_ip():
    return {"ip": socket_ip}

@app.get("/")
async def get():
    websocket_token = os.getenv("WEBSOCKET_TOKEN", "Northway12121")
    dictionary = load_dictionary()
    languages = dictionary.get("supported_languages", [])
    language_options = "".join([
        f'<option value="{lang["code"]}"{" selected" if lang["code"] == "en-US" else ""}>{lang["name"]}</option>\n' 
        for lang in languages
    ])
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "Northway12121")
    return HTMLResponse(
        ROOT_TEMPLATE
        .replace("{{WEBSOCKET_TOKEN}}", websocket_token)
        .replace("{{LANGUAGE_OPTIONS}}", language_options)
        .replace("{{ADMIN_USERNAME}}", admin_username)
        .replace("{{ADMIN_PASSWORD}}", admin_password)
    )

@app.get("/dashboard", dependencies=[Depends(get_current_username)])
async def dashboard():
    dashboard_path = os.path.join(CURRENT_DIR, "dashboard.html")
    websocket_token = os.getenv("WEBSOCKET_TOKEN", "Northway12121")
    if not os.path.exists(dashboard_path):
        raise HTTPException(status_code=404, detail="Dashboard page not found")
    with open(dashboard_path, "r") as f:
        dashboard_content = f.read()
    return HTMLResponse(dashboard_content.replace("{{WEBSOCKET_TOKEN}}", websocket_token))

@app.get("/user")
async def preview():
    websocket_token = os.getenv("WEBSOCKET_TOKEN", "Northway12121")
    dictionary = load_dictionary()
    languages = dictionary.get("supported_languages", [])
    language_options = "".join([
        f'<option value="{lang["code"]}"{" selected" if lang["code"] == "en-US" else ""}>{lang["name"]}</option>\n' 
        for lang in languages
    ])
    
    # Create response with explicit headers to prevent authentication prompts
    response = HTMLResponse(
        USER_TEMPLATE
        .replace("{{WEBSOCKET_TOKEN}}", websocket_token)
        .replace("{{LANGUAGE_OPTIONS}}", language_options)
    )
    
    # Add comprehensive headers to prevent authentication caching and prompts
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Explicitly remove any authentication headers that might be cached
    if "WWW-Authenticate" in response.headers:
        del response.headers["WWW-Authenticate"]
    if "Authorization" in response.headers:
        del response.headers["Authorization"]
    
    log_message(logging.INFO, "User page accessed - no authentication required")
    
    return response

@app.get("/setup")
async def setup():
    return HTMLResponse(SETUP_TEMPLATE)

@app.get("/audio_devices")
async def get_audio_devices():
    devices = sd.query_devices()
    return [{"name": device["name"], "index": i} for i, device in enumerate(devices)]

# -------------------------------------------------------------------
# GitHub Update Endpoints
# -------------------------------------------------------------------
@app.get("/check_updates", dependencies=[Depends(get_current_username)])
async def check_updates():
    """Check for GitHub updates"""
    try:
        from github_updater import GitHubUpdater
        updater = GitHubUpdater()
        status = updater.get_update_status_display()
        return status
    except Exception as e:
        log_message(logging.ERROR, f"Error checking for updates: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

@app.post("/apply_update", dependencies=[Depends(get_current_username)])
async def apply_update():
    """Apply GitHub update"""
    try:
        from github_updater import GitHubUpdater
        updater = GitHubUpdater()
        
        # Check if update is available first
        status = updater.check_for_updates()
        if status['status'] != 'update_available':
            return {
                'status': 'error',
                'message': 'No update available'
            }
        
        # Create backup
        backup_dir = updater.backup_current_version()
        if not backup_dir:
            return {
                'status': 'error',
                'message': 'Failed to create backup'
            }
        
        # Apply update
        if updater.apply_update():
            log_message(logging.INFO, "Update applied successfully via dashboard")
            return {
                'status': 'success',
                'message': 'Update applied successfully',
                'backup_dir': backup_dir
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to apply update'
            }
            
    except Exception as e:
        log_message(logging.ERROR, f"Error applying update: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

@app.post("/perform_update", dependencies=[Depends(get_current_username)])
async def perform_update():
    """Perform GitHub update"""
    try:
        from github_updater import GitHubUpdater
        updater = GitHubUpdater()
        result = updater.perform_update()
        
        if result['status'] == 'success':
            log_message(logging.INFO, "GitHub update completed successfully")
            # Broadcast update notification to all clients
            await broadcast_update_notification(result)
        else:
            log_message(logging.ERROR, f"GitHub update failed: {result['message']}")
        
        return result
    except Exception as e:
        log_message(logging.ERROR, f"Error performing update: {e}")
        return {
            'status': 'error',
            'message': f'Error performing update: {str(e)}'
        }

async def broadcast_update_notification(update_result):
    """Broadcast update notification to all connected clients"""
    for client in clients:
        try:
            await client.send_text(json.dumps({
                "type": "update_notification", 
                "result": update_result
            }))
            log_message(logging.DEBUG, f"Sent update notification to client: {client.client}")
        except Exception as e:
            log_message(logging.ERROR, f"WebSocket send error for update notification: {e}")
            clients.remove(client)

@app.post("/setup")
async def set_setup(setup: dict):
    device_index = setup.get("audio_device")
    model_path = setup.get("model_path")
    if device_index is not None:
        try:
            sd.default.device = int(device_index)
            log_message(logging.INFO, f"Set audio device to index {device_index}")
        except Exception as e:
            log_message(logging.ERROR, f"Failed to set audio device: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to set audio device: {e}")
    if model_path:
        CONFIG["model_path"] = model_path
        log_message(logging.INFO, f"Updated Vosk model path to {model_path}")
    return {"status": "success"}

@app.get("/settings", dependencies=[Depends(get_current_username)])
async def get_settings():
    return CONFIG

@app.post("/settings", dependencies=[Depends(get_current_username)])
async def set_settings(new_config: dict):
    allowed_keys = [
        "font_size", "font_style", "bg_color", "text_color", "max_line_length", "max_lines",
        "text_justify", "text_anchor", "text_padding_x", "text_padding_y",
        "main_text_position_x", "main_text_position_y",
        "preview_position", "preview_fine_tune_x", "preview_fine_tune_y"
    ]
    valid_config = {k: v for k, v in new_config.items() if k in allowed_keys}
    CONFIG.update(valid_config)
    log_message(logging.INFO, f"Settings updated via API: {valid_config}")
    try:
        await broadcast_settings(valid_config)
        log_message(logging.DEBUG, f"Settings broadcasted to {len(clients)} clients")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to broadcast settings: {e}")
    return {"status": "success"}

async def broadcast_settings(settings):
    for client in clients:
        try:
            await client.send_text(json.dumps({"type": "settings", "settings": settings}))
            log_message(logging.DEBUG, f"Sent settings to client: {client.client}")
        except Exception as e:
            log_message(logging.ERROR, f"WebSocket send error for settings: {e}")
            clients.remove(client)

@app.get("/schedule", dependencies=[Depends(get_current_username)])
async def get_schedule():
    return load_schedule()

@app.post("/schedule", dependencies=[Depends(get_current_username)])
async def set_schedule(schedule: dict):
    date_str = schedule.get("date", "").strip()
    start_time = schedule.get("start_time", "").strip()
    stop_time = schedule.get("stop_time", "").strip()
    timezone = schedule.get("timezone", "America/New_York").strip()
    pause_event = schedule.get("pause_event", False)
    repeats = schedule.get("repeats", False)
    recurrence_type = schedule.get("recurrence_type", "one-time").strip()
    recurrence_interval = schedule.get("recurrence_interval", 1)  # Every X days/weeks/months

    ending_type = schedule.get("ending_type", "never")  # "never", "after_occurrences", "on_date"
    ending_occurrences = schedule.get("ending_occurrences", None)
    ending_date = schedule.get("ending_date", None)
    
    log_message(logging.DEBUG, f"Received advanced schedule: date={date_str}, start_time={start_time}, stop_time={stop_time}, timezone={timezone}, pause_event={pause_event}, repeats={repeats}, recurrence_type={recurrence_type}")

    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        log_message(logging.WARNING, f"Invalid date format: {date_str}")
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")

    if not start_time or not validate_time_format(start_time):
        log_message(logging.WARNING, f"Invalid start time format: {start_time}")
        raise HTTPException(status_code=400, detail="Invalid start time format (use HH:MM)")

    if not stop_time or not validate_time_format(stop_time):
        log_message(logging.WARNING, f"Invalid stop time format: {stop_time}")
        raise HTTPException(status_code=400, detail="Invalid stop time format (use HH:MM)")

    valid_recurrence_types = ['one-time', 'weekly', 'monthly', 'yearly']
    if recurrence_type not in valid_recurrence_types:
        log_message(logging.WARNING, f"Invalid recurrence type: {recurrence_type}")
        raise HTTPException(status_code=400, detail=f"Invalid recurrence type (use one of: {', '.join(valid_recurrence_types)})")

    new_schedule = {
        "date": date_str,
        "start_time": start_time,
        "stop_time": stop_time,
        "timezone": timezone,
        "pause_event": pause_event,
        "repeats": repeats,
        "recurrence_type": recurrence_type,
        "recurrence_interval": recurrence_interval,

        "ending_type": ending_type,
        "ending_occurrences": ending_occurrences,
        "ending_date": ending_date
    }
    
    schedules = load_schedule()
    # Check if we're updating an existing schedule
    existing_schedule_index = next((i for i, s in enumerate(schedules) if s['date'] == date_str), None)
    
    if existing_schedule_index is not None:
        # Update existing schedule
        schedules[existing_schedule_index] = new_schedule
        log_message(logging.INFO, f"Updated existing schedule: date={date_str}, start={start_time}, stop={stop_time}, timezone={timezone}, recurrence_type={recurrence_type}")
    else:
        # Add new schedule
        schedules.append(new_schedule)
        log_message(logging.INFO, f"Added new schedule: date={date_str}, start={start_time}, stop={stop_time}, timezone={timezone}, recurrence_type={recurrence_type}")
    
    save_schedule(schedules)
    schedule_recognition(schedules)
    return {"status": "success"}

@app.delete("/schedule", dependencies=[Depends(get_current_username)])
async def delete_schedule(date: str = Query(...)):
    schedules = load_schedule()
    updated_schedules = [s for s in schedules if s['date'] != date]
    if len(updated_schedules) == len(schedules):
        log_message(logging.WARNING, f"No schedule found for date: {date}")
        raise HTTPException(status_code=404, detail=f"No schedule found for {date}")
    save_schedule(updated_schedules)
    schedule_recognition(updated_schedules)
    log_message(logging.INFO, f"Schedule deleted for date: {date}")
    return {"status": "success"}

@app.get("/schedule/timezones", dependencies=[Depends(get_current_username)])
async def get_timezones():
    """Get list of available timezones"""
    import pytz
    return {"timezones": list(pytz.all_timezones)}

@app.get("/schedule/recurrence_options", dependencies=[Depends(get_current_username)])
async def get_recurrence_options():
    """Get available recurrence options for the frontend"""
    return {
        "recurrence_types": ["one-time", "weekly", "monthly", "yearly"],
        "ending_types": ["never", "after_occurrences", "on_date"]
    }

@app.get("/dictionary", dependencies=[Depends(get_current_username)])
async def get_dictionary():
    dictionary = load_dictionary()
    log_message(logging.DEBUG, "Dictionary endpoint accessed")
    return dictionary

@app.post("/dictionary/spelling", dependencies=[Depends(get_current_username)])
async def add_spelling_correction(correction: dict):
    incorrect = correction.get("incorrect", "").strip()
    correct = correction.get("correct", "").strip()
    if not incorrect or not correct:
        raise HTTPException(status_code=400, detail="Both incorrect and correct fields are required")
    dictionary = load_dictionary()
    dictionary["spelling_corrections"][incorrect] = correct
    save_dictionary(dictionary)
    log_message(logging.INFO, f"Added spelling correction: {incorrect} -> {correct}")
    return {"status": "success"}

@app.post("/dictionary/phrase", dependencies=[Depends(get_current_username)])
async def add_custom_phrase(phrase: dict):
    phrase_text = phrase.get("phrase", "").strip()
    if not phrase_text:
        raise HTTPException(status_code=400, detail="Phrase field is required")
    dictionary = load_dictionary()
    if phrase_text not in dictionary["custom_phrases"]:
        dictionary["custom_phrases"].append(phrase_text)
        dictionary["custom_phrases"].sort()
        save_dictionary(dictionary)
        log_message(logging.INFO, f"Added custom phrase: {phrase_text}")
    return {"status": "success"}

@app.post("/dictionary/bible_book", dependencies=[Depends(get_current_username)])
async def add_bible_book(book: dict):
    book_name = book.get("book", "").strip()
    if not book_name:
        raise HTTPException(status_code=400, detail="Book name field is required")
    dictionary = load_dictionary()
    if book_name not in dictionary["bible_books"]:
        dictionary["bible_books"].append(book_name)
        dictionary["bible_books"].sort()
        save_dictionary(dictionary)
        log_message(logging.INFO, f"Added Bible book: {book_name}")
    return {"status": "success"}

@app.delete("/dictionary/spelling", dependencies=[Depends(get_current_username)])
async def delete_spelling_correction(incorrect: str = Query(...)):
    dictionary = load_dictionary()
    if incorrect in dictionary["spelling_corrections"]:
        del dictionary["spelling_corrections"][incorrect]
        save_dictionary(dictionary)
        log_message(logging.INFO, f"Deleted spelling correction: {incorrect}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail=f"Spelling correction not found: {incorrect}")

@app.delete("/dictionary/phrase", dependencies=[Depends(get_current_username)])
async def delete_custom_phrase(phrase: str = Query(...)):
    dictionary = load_dictionary()
    if phrase in dictionary["custom_phrases"]:
        dictionary["custom_phrases"].remove(phrase)
        save_dictionary(dictionary)
        log_message(logging.INFO, f"Deleted custom phrase: {phrase}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail=f"Custom phrase not found: {phrase}")

@app.delete("/dictionary/bible_book", dependencies=[Depends(get_current_username)])
async def delete_bible_book(book: str = Query(...)):
    dictionary = load_dictionary()
    if book in dictionary["bible_books"]:
        dictionary["bible_books"].remove(book)
        save_dictionary(dictionary)
        log_message(logging.INFO, f"Deleted Bible book: {book}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail=f"Bible book not found: {book}")

@app.get("/dictionary_page", dependencies=[Depends(get_current_username)])
async def dictionary_page():
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "Northway12121")
    return HTMLResponse(
        DICTIONARY_PAGE_TEMPLATE
        .replace("{{ADMIN_USERNAME}}", admin_username)
        .replace("{{ADMIN_PASSWORD}}", admin_password)
    )

@app.post("/start_recognition", dependencies=[Depends(get_current_username)])
async def start_recognition_endpoint():
    global production_caption_history
    log_message(logging.INFO, "Received request to start recognition")
    try:
        await start_recognition()
        # Clear production caption history when starting recognition
        production_caption_history = ""
        log_message(logging.INFO, "Speech recognition started successfully")
        return {"status": "success", "message": "Speech recognition started"}
    except Exception as e:
        log_message(logging.ERROR, f"Failed to start recognition via API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start recognition: {str(e)}")

@app.post("/stop_recognition", dependencies=[Depends(get_current_username)])
async def stop_recognition_endpoint():
    global production_caption_history
    log_message(logging.INFO, "Received request to stop recognition")
    try:
        await stop_recognition()
        # Clear production caption history when stopping recognition
        production_caption_history = ""
        log_message(logging.INFO, "Speech recognition stopped successfully")
        return {"status": "success", "message": "Speech recognition stopped"}
    except Exception as e:
        log_message(logging.ERROR, f"Failed to stop recognition via API: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop recognition: {str(e)}")

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/user_no_auth")
async def user_no_auth_check():
    """Explicitly check that user route requires no authentication"""
    return {
        "message": "User route requires no authentication",
        "status": "no_auth_required",
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/captions")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    correct_token = os.getenv("WEBSOCKET_TOKEN", "Northway12121")
    if token != correct_token:
        log_message(logging.WARNING, f"WebSocket connection rejected: Invalid token '{token}'")
        await websocket.close(code=1008, reason="Invalid token")
        return
    await websocket.accept()
    clients.append(websocket)
    log_message(logging.INFO, f"WebSocket client connected: {websocket.client}")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "language":
                    log_message(logging.INFO, f"Ignoring language change request from client: {message.get('language')}")
                else:
                    for client in clients:
                        try:
                            await client.send_text(json.dumps({"type": "caption", "text": message}))
                            log_message(logging.DEBUG, f"Sent data to client: {client.client}")
                        except Exception as e:
                            log_message(logging.ERROR, f"WebSocket send error: {e}")
            except json.JSONDecodeError:
                for client in clients:
                    try:
                        await client.send_text(json.dumps({"type": "caption", "text": data}))
                        log_message(logging.DEBUG, f"Sent data to client: {client.client}")
                    except Exception as e:
                        log_message(logging.ERROR, f"WebSocket send error: {e}")
    except Exception as e:
        log_message(logging.ERROR, f"WebSocket error: {e}")
    finally:
        clients.remove(websocket)
        log_message(logging.INFO, f"WebSocket client disconnected: {websocket.client}")

async def send_caption_to_clients(translations, languages, caption_type="production"):
    """
    Send captions to clients with proper structure for frontend
    caption_type: "production", "user", "translation", or "user_translations"
    """
    # Structure the data according to what the frontend expects
    if caption_type == "production":
        structured_data = {"production": translations}
    elif caption_type == "user":
        structured_data = {"user": translations}
    elif caption_type == "user_translations":
        structured_data = {"user_translations": translations}
    else:  # translation
        structured_data = {"production": translations}  # Translations go to production view
    
    for client in clients:
        try:
            await client.send_text(json.dumps({
                "type": "caption", 
                "translations": structured_data, 
                "languages": languages
            }))
            log_message(logging.DEBUG, f"Sent {caption_type} caption to client: {client.client}")
        except Exception as e:
            log_message(logging.ERROR, f"WebSocket send error: {e}")
            clients.remove(client)

def run_fastapi():
    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            log_message(logging.INFO, "Attempting to start FastAPI server on 0.0.0.0:8000")
            # Start the server in a separate thread to allow browser opening
            def start_server():
                uvicorn.run(app, host="0.0.0.0", port=8000)
            
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Open the dashboard in the default browser
            try:
                webbrowser.open("http://localhost:8000/dashboard")
                log_message(logging.INFO, "Dashboard opened in browser")
            except Exception as e:
                log_message(logging.WARNING, f"Failed to open browser: {e}")
            
            log_message(logging.INFO, "FastAPI server started successfully on 0.0.0.0:8000")
            return
        except Exception as e:
            log_message(logging.ERROR, f"Failed to start FastAPI server (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    log_message(logging.CRITICAL, "FastAPI server failed to start after all retries.")

fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
fastapi_thread.start()
time.sleep(1)

# -------------------------------------------------------------------
# Vosk Speech Recognition Setup (will be initialized after callbacks are defined)
# -------------------------------------------------------------------
vosk_recognizer = None  # Will be initialized later

is_recognizing = False
should_be_recognizing = False

# -------------------------------------------------------------------
# Text Processing
# -------------------------------------------------------------------
transcript = []
last_caption = ""

# Production view caption state (separate from user view)
production_caption_update_translations = {"en-US": ""}
production_caption = ""
production_caption_history = ""  # Store the accumulated production caption text
production_last_event_time = time.time()  # For pause detection between utterances

# User view caption state (completely separate)
user_caption = ""
user_caption_update_pending = False
user_caption_history = {}  # Dictionary to store history for each language
user_last_text = {}  # Dictionary to store interim text for each language
current_user_language = "en-US"  # Track currently selected language in user view

# Auto-finalization timing for user view
user_auto_finalize_timer = None
user_speech_start_time = {}  # Dictionary to track when speech started for each language

# Initialize history for all supported languages
dictionary = load_dictionary()
for lang in dictionary.get("supported_languages", []):
    user_caption_history[lang["code"]] = []
    user_last_text[lang["code"]] = ""

dictionary = load_dictionary()
bible_books = dictionary["bible_books"]
spelling_corrections_dict = dictionary["spelling_corrections"]
custom_phrases = dictionary["custom_phrases"]

def spelling_corrections(text):
    words = text.split()
    return " ".join([spelling_corrections_dict.get(word.lower(), word) for word in words])

def correct_bible_books(text):
    return " ".join([word.capitalize() if word.lower() in [b.lower() for b in bible_books] else word for word in text.split()])

def apply_text_corrections(text):
    return correct_bible_books(spelling_corrections(text))

def map_vosk_language_code(vosk_code):
    """Map Vosk language codes to dictionary language codes"""
    # Vosk primarily supports English, but we keep this for future expansion
    mapping = {
        'en-US': 'en-US',
        'en': 'en-US'
    }
    return mapping.get(vosk_code, 'en-US')

def auto_finalize_user_speech():
    """Auto-finalize user speech after the specified delay"""
    global user_auto_finalize_timer, user_last_text, user_caption_history, user_speech_start_time
    
    auto_finalize_delay = USER_SETTINGS.get("user_auto_finalize_delay", 10.0)
    log_message(logging.INFO, f"Auto-finalizing user speech after {auto_finalize_delay} seconds")
    
    # Process each language that has interim text
    for lang, interim_text in user_last_text.items():
        if interim_text and interim_text.strip() != "":
            # Add the interim text to history as a finalized caption
            if not user_caption_history[lang] or interim_text != user_caption_history[lang][-1]:
                user_caption_history[lang].append(interim_text)
                # Keep only the last user_max_lines captions
                user_max_lines = USER_SETTINGS.get("user_lines", 3)
                if len(user_caption_history[lang]) > user_max_lines:
                    user_caption_history[lang] = user_caption_history[lang][-user_max_lines:]
            
            # Clear the interim text
            user_last_text[lang] = ""
            
            # Reset speech timing for this language
            if lang in user_speech_start_time:
                del user_speech_start_time[lang]
    
    # Reset the timer
    user_auto_finalize_timer = None
    
    # Send updated captions to clients
    if not user_caption_update_pending:
        user_caption_update_pending = True
        Timer(0.1, debounce_update_user_caption).start()

def check_and_clear_on_pause():
    """Check if a pause has been detected and clear the production display if needed"""
    global production_caption, production_caption_history, production_last_event_time
    
    # Get pause threshold from config (default 2 seconds)
    pause_threshold = CONFIG.get("pause_threshold_seconds", 2.0)
    
    # Check if enough time has passed since last speech event
    time_since_last_event = time.time() - production_last_event_time
    
    if time_since_last_event > pause_threshold:
        # Pause detected - clear the current display
        if production_caption.strip():  # Only clear if there's something to clear
            log_message(logging.INFO, f"Pause detected ({time_since_last_event:.1f}s), clearing production display")
            production_caption = ""
            # Don't clear history - keep it for transcript purposes
            # But we could optionally clear it here if you want a complete fresh start

# Production view processing (hybrid approach: fresh text + pause detection)
def process_production_speech_text(text=None, translations=None, is_recognized=False):
    global transcript, production_caption_update_translations, last_caption, production_caption, production_caption_history, production_last_event_time
    if translations is None:
        translations = {}
    if text:
        translations["en-US"] = text
    corrected_translations = {lang: apply_text_corrections(t) for lang, t in translations.items() if t}
    
    # Process English captions for production view
    if "en-US" in corrected_translations:
        corrected_text = corrected_translations["en-US"]
        
        # Update last event time for pause detection (regardless of recognition status)
        production_last_event_time = time.time()
        
        # Use production settings for line wrapping
        prod_line_length = CONFIG.get("max_line_length", 90)
        
        if is_recognized:
            # For finalized captions, add to transcript and update history
            transcript.append(corrected_text)
            if len(transcript) > CONFIG["max_transcript_lines"]:
                transcript = transcript[-CONFIG["max_transcript_lines"]:]
            
            # Update production caption history for context (but don't use for display)
            if production_caption_history:
                production_caption_history += " " + corrected_text
            else:
                production_caption_history = corrected_text
            
            # For production view, show ONLY the current finalized text (fresh approach)
            wrapped_lines = textwrap.wrap(corrected_text, width=prod_line_length, break_long_words=False, break_on_hyphens=False)
            production_caption = wrapped_lines[-1] if wrapped_lines else ""
            
        else:
            # For interim captions, show ONLY the current interim text (fresh approach)
            wrapped_lines = textwrap.wrap(corrected_text, width=prod_line_length, break_long_words=False, break_on_hyphens=False)
            production_caption = wrapped_lines[-1] if wrapped_lines else ""
    
    # Production view only shows English captions
    production_caption_update_translations = {"en-US": production_caption}
    
    # Check for pause detection and clear display if needed
    check_and_clear_on_pause()
    
    # Send updates immediately for production view (no debounce for real-time)
    if "en-US" in production_caption_update_translations:
        try:
            asyncio.run(send_caption_to_clients(production_caption_update_translations, languages=["en-US"], caption_type="production"))
        except Exception as e:
            log_message(logging.ERROR, f"Failed to send production caption: {e}")
    
    last_caption = production_caption
    return production_caption_update_translations

# User view processing (separate from production)
def process_user_speech_text(text=None, translations=None, is_recognized=False):
    global user_caption, user_caption_update_pending, user_caption_history, user_last_text, user_auto_finalize_timer, user_speech_start_time
    if translations is None:
        translations = {}
    if text:
        translations["en-US"] = text
    
    log_message(logging.DEBUG, f"process_user_speech_text called: is_recognized={is_recognized}, translations={list(translations.keys())}")
    
    corrected_translations = {lang: apply_text_corrections(t) for lang, t in translations.items() if t}
    
    log_message(logging.DEBUG, f"corrected_translations: {list(corrected_translations.keys())}")
    
    # Use user settings for line wrapping and number of lines
    user_line_length = USER_SETTINGS.get("user_max_line_length", CONFIG["max_line_length"])
    user_max_lines = USER_SETTINGS.get("user_lines", 3)
    
    # Process each language
    for lang, corrected_text in corrected_translations.items():
        if is_recognized:
            # For final captions, add to history if it's new and not empty
            if corrected_text.strip() != "":
                # Only add to history if it's different from the last caption
                if not user_caption_history[lang] or corrected_text != user_caption_history[lang][-1]:
                    user_caption_history[lang].append(corrected_text)
                    # Keep only the last user_max_lines captions
                    if len(user_caption_history[lang]) > user_max_lines:
                        user_caption_history[lang] = user_caption_history[lang][-user_max_lines:]
                user_last_text[lang] = ""  # Clear interim text
                
                # Cancel auto-finalization timer since we got a final result
                if user_auto_finalize_timer:
                    user_auto_finalize_timer.cancel()
                    user_auto_finalize_timer = None
                    log_message(logging.DEBUG, "Cancelled auto-finalization timer due to final recognition")
        else:
            # For interim captions, update the current text
            user_last_text[lang] = corrected_text
            
            # Start or reset auto-finalization timer for this language
            if lang not in user_speech_start_time:
                user_speech_start_time[lang] = time.time()
                log_message(logging.DEBUG, f"Started speech timing for {lang}")
            
            # Cancel existing timer if it exists
            if user_auto_finalize_timer:
                user_auto_finalize_timer.cancel()
            
            # Start new auto-finalization timer
            auto_finalize_delay = USER_SETTINGS.get("user_auto_finalize_delay", 10.0)
            user_auto_finalize_timer = Timer(auto_finalize_delay, auto_finalize_user_speech)
            user_auto_finalize_timer.start()
            log_message(logging.DEBUG, f"Started auto-finalization timer for {lang} ({auto_finalize_delay} seconds)")
        
        # Build the display text from history and current interim text
        display_lines = []
        
        # Add all history items
        for caption in user_caption_history[lang]:
            # Wrap each caption according to line length
            wrapped_lines = textwrap.wrap(caption, width=user_line_length)
            display_lines.extend(wrapped_lines)
        
        # Add current interim caption if it exists
        if user_last_text[lang] and user_last_text[lang].strip() != "":
            wrapped_lines = textwrap.wrap(user_last_text[lang], width=user_line_length)
            display_lines.extend(wrapped_lines)
        
        # Join all lines with newlines for display
        user_caption = "\n".join(display_lines) if display_lines else ""
        
        log_message(logging.DEBUG, f"User caption updated for {lang}: {user_caption}")
        
        # Send user caption update
        if not user_caption_update_pending:
            user_caption_update_pending = True
            log_message(logging.DEBUG, f"Setting user_caption_update_pending=True for languages: {list(corrected_translations.keys())}")
            Timer(0.1, debounce_update_user_caption).start()
        else:
            log_message(logging.DEBUG, f"user_caption_update_pending already True, skipping Timer")

def debounce_update_user_caption():
    global user_caption_update_pending, user_caption, user_caption_history, user_last_text
    if user_caption_update_pending:
        try:
            # Create a translations object with all languages and their histories
            all_translations = {}
            for lang, history in user_caption_history.items():
                if history:  # Only include languages that have history
                    # Join all history items with newlines
                    all_translations[lang] = "\n".join(history)
            
            # Also include current interim text for each language
            for lang, interim_text in user_last_text.items():
                if interim_text and interim_text.strip() != "":
                    if lang in all_translations:
                        all_translations[lang] += "\n" + interim_text
                    else:
                        all_translations[lang] = interim_text
            
            if all_translations:
                log_message(logging.DEBUG, f"debounce_update_user_caption: sending translations for languages: {list(all_translations.keys())}")
                log_message(logging.DEBUG, f"debounce_update_user_caption: sample translation content: {list(all_translations.items())[:2]}")
                asyncio.run(send_caption_to_clients(all_translations, languages=list(all_translations.keys()), caption_type="user"))
                log_message(logging.DEBUG, f"Sent user captions with history for all languages: {list(all_translations.keys())}")
            else:
                log_message(logging.DEBUG, f"debounce_update_user_caption: no translations to send")
        except Exception as e:
            log_message(logging.ERROR, f"Failed to send user caption: {e}")
        user_caption_update_pending = False





# -------------------------------------------------------------------
# Vosk Speech Recognition Event Handlers
# -------------------------------------------------------------------
def on_vosk_recognizing(text):
    """Handle partial recognition results from Vosk"""
    global last_caption
    log_message(logging.DEBUG, f"Vosk recognizing: {text}")
    
    # Process for production view
    process_production_speech_text(text=text, is_recognized=False)
    
    # Also process for user view when English is selected
    if current_user_language == "en-US":
        process_user_speech_text(text=text, is_recognized=False)

def on_vosk_recognized(text):
    """Handle final recognition results from Vosk"""
    global last_caption
    log_message(logging.DEBUG, f"Vosk recognized: {text}")
    
    # Process for production view
    process_production_speech_text(text=text, is_recognized=True)
    
    # Also process for user view when English is selected
    if current_user_language == "en-US":
        process_user_speech_text(text=text, is_recognized=True)

def on_vosk_error(error_msg):
    """Handle errors from Vosk recognition"""
    global is_recognizing
    log_message(logging.ERROR, f"Vosk recognition error: {error_msg}")
    
    try:
        asyncio.run(send_caption_to_clients({"en-US": f"Recognition error: {error_msg}"}, languages=["en-US"], caption_type="production"))
    except Exception as e:
        log_message(logging.ERROR, f"Failed to send error caption: {e}")
    
    is_recognizing = False

# Initialize Vosk recognizer after callbacks are defined
vosk_recognizer = VoskSpeechRecognizer(
    model_path=CONFIG["model_path"],
    sample_rate=CONFIG.get("sample_rate", 16000),
    chunk_size=CONFIG.get("audio_chunk_size", 4000)
)

# Set up callbacks for Vosk recognizer
vosk_recognizer.set_callbacks(
    on_recognizing=on_vosk_recognizing,
    on_recognized=on_vosk_recognized,
    on_error=on_vosk_error
)

log_message(logging.INFO, "Vosk speech recognizer initialized successfully")

# -------------------------------------------------------------------
# Transcript Saving
# -------------------------------------------------------------------
@app.post("/save_transcript")
async def save_transcript():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(CURRENT_DIR, f"transcript_{timestamp}.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(transcript))
        log_message(logging.INFO, f"Transcript saved to {file_path}")
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        log_message(logging.ERROR, f"Failed to save transcript: {e}")
        raise HTTPException(status_code=500, detail="Failed to save transcript")

# -------------------------------------------------------------------
# Start/Stop Recognition
# -------------------------------------------------------------------
async def start_recognition():
    global vosk_recognizer, is_recognizing, should_be_recognizing
    max_retries = 3
    for attempt in range(max_retries):
        try:
            log_message(logging.INFO, f"Starting Vosk recognition (attempt {attempt + 1}/{max_retries})")
            
            # Note: Vosk doesn't support phrase lists like Azure, but we can implement
            # custom post-processing for dictionary terms if needed
            
            await send_caption_to_clients({"en-US": "Listening..."}, languages=["en-US"], caption_type="production")
            
            # Start Vosk recognizer
            vosk_recognizer.start_recognition()
            
            is_recognizing = True
            should_be_recognizing = True
            log_message(logging.INFO, "Vosk recognition started successfully")
            return
        except Exception as e:
            log_message(logging.ERROR, f"Failed to start Vosk recognition (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Recreate recognizer on retry
                try:
                    vosk_recognizer.stop_recognition()
                except:
                    pass
                
                vosk_recognizer = VoskSpeechRecognizer(
                    model_path=CONFIG["model_path"],
                    sample_rate=CONFIG.get("sample_rate", 16000),
                    chunk_size=CONFIG.get("audio_chunk_size", 4000)
                )
                
                # Reconnect callbacks
                vosk_recognizer.set_callbacks(
                    on_recognizing=on_vosk_recognizing,
                    on_recognized=on_vosk_recognized,
                    on_error=on_vosk_error
                )
            else:
                try:
                    await send_caption_to_clients({"en-US": "Error: Failed to start speech recognition."}, languages=["en-US"], caption_type="production")
                except Exception as e2:
                    log_message(logging.ERROR, f"Failed to send error caption: {e2}")
                is_recognizing = False
                should_be_recognizing = False
                raise HTTPException(status_code=500, detail=f"Failed to start recognition after {max_retries} attempts: {e}")

async def stop_recognition():
    global is_recognizing, should_be_recognizing
    log_message(logging.INFO, "Stopping Vosk recognition")
    try:
        vosk_recognizer.stop_recognition()
        await send_caption_to_clients({"en-US": "Recognition stopped."}, languages=["en-US"], caption_type="production")
        is_recognizing = False
        should_be_recognizing = False
        log_message(logging.INFO, "Vosk recognition stopped successfully")
    except Exception as e:
        log_message(logging.ERROR, f"Error stopping Vosk recognition: {e}")
        try:
            await send_caption_to_clients({"en-US": "Error: Failed to stop recognition."}, languages=["en-US"], caption_type="production")
        except Exception as e2:
            log_message(logging.ERROR, f"Failed to send error caption: {e2}")
        is_recognizing = False
        should_be_recognizing = False
        raise HTTPException(status_code=500, detail=f"Failed to stop recognition: {e}")

# -------------------------------------------------------------------
# Scheduler
# -------------------------------------------------------------------
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

def validate_time_format(time_str):
    pattern = r"^(?:(?:[01]?\d|2[0-3]):[0-5]\d)$"
    return bool(re.match(pattern, time_str))



def schedule_recognition(schedules):
    global should_be_recognizing
    schedule.clear()
    
    for s in schedules:
        try:
            # Extract schedule parameters
            date_str = s.get('date')
            start_time = s.get('start_time')
            stop_time = s.get('stop_time')
            timezone = s.get('timezone', 'America/New_York')
            pause_event = s.get('pause_event', False)
            repeats = s.get('repeats', False)
            recurrence_type = s.get('recurrence_type', 'one-time')
            recurrence_interval = s.get('recurrence_interval', 1)
            recurrence_pattern = s.get('recurrence_pattern', 'on_day')
            recurrence_day = s.get('recurrence_day', 1)
            recurrence_weekday = s.get('recurrence_weekday', 'Sunday')
            recurrence_weekday_ordinal = s.get('recurrence_weekday_ordinal', 'First')
            ending_type = s.get('ending_type', 'never')
            ending_occurrences = s.get('ending_occurrences')
            ending_date = s.get('ending_date')
            
            # Skip if pause event is enabled
            if pause_event:
                log_message(logging.INFO, f"Schedule {date_str} is paused - skipping")
                continue
                
            # Skip if repeats is disabled
            if not repeats and recurrence_type != 'one-time':
                log_message(logging.INFO, f"Schedule {date_str} has repeats disabled - treating as one-time")
                recurrence_type = 'one-time'
            
            # Check if schedule should end
            if ending_type == 'after_occurrences' and ending_occurrences:
                # TODO: Implement occurrence counting
                pass
            elif ending_type == 'on_date' and ending_date:
                try:
                    end_date = datetime.strptime(ending_date, '%Y-%m-%d').date()
                    if datetime.now().date() > end_date:
                        log_message(logging.INFO, f"Schedule {date_str} has ended - skipping")
                        continue
                except ValueError:
                    log_message(logging.WARNING, f"Invalid ending date format: {ending_date}")
            
            if start_time and validate_time_format(start_time):
                # Create start task
                def create_start_task(schedule_info):
                    def start_task():
                        global should_be_recognizing
                        should_be_recognizing = True
                        asyncio.run(start_recognition())
                        log_message(logging.INFO, f"Started recognition for schedule: {schedule_info['date']} at {schedule_info['start_time']}")
                    return start_task
                
                # Create stop task if stop time is available
                def create_stop_task(schedule_info):
                    def stop_task():
                        global should_be_recognizing
                        should_be_recognizing = False
                        asyncio.run(stop_recognition())
                        log_message(logging.INFO, f"Stopped recognition for schedule: {schedule_info['date']} at {schedule_info['stop_time']}")
                    return stop_task
                
                schedule_info = {
                    'date': date_str,
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'recurrence_type': recurrence_type
                }
                
                if recurrence_type == 'one-time':
                    # One-time schedule
                    schedule.every().day.at(start_time).do(create_start_task(schedule_info))
                    if stop_time:
                        schedule.every().day.at(stop_time).do(create_stop_task(schedule_info))
                    log_message(logging.INFO, f"Scheduled one-time: {date_str} {start_time}-{stop_time}")
                    
                elif recurrence_type == 'weekly':
                    # Weekly schedule
                    schedule_date = datetime.strptime(date_str, '%Y-%m-%d')
                    weekday = schedule_date.strftime('%A').lower()
                    getattr(schedule.every(), weekday).at(start_time).do(create_start_task(schedule_info))
                    if stop_time:
                        getattr(schedule.every(), weekday).at(stop_time).do(create_stop_task(schedule_info))
                    log_message(logging.INFO, f"Scheduled weekly: every {weekday} {start_time}-{stop_time}")
                    
                elif recurrence_type == 'monthly':
                    # Monthly schedule - repeat on the same day of month as the initial date
                    schedule.every().day.at(start_time).do(create_start_task(schedule_info))
                    if stop_time:
                        schedule.every().day.at(stop_time).do(create_stop_task(schedule_info))
                    log_message(logging.INFO, f"Scheduled monthly: same day of month {start_time}-{stop_time}")
                        
                elif recurrence_type == 'yearly':
                    # Yearly schedule
                    schedule_date = datetime.strptime(date_str, '%Y-%m-%d')
                    month_day = schedule_date.strftime('%m-%d')
                    schedule.every().day.at(start_time).do(create_start_task(schedule_info))
                    if stop_time:
                        schedule.every().day.at(stop_time).do(create_stop_task(schedule_info))
                    log_message(logging.INFO, f"Scheduled yearly: {month_day} {start_time}-{stop_time}")
                    
        except Exception as e:
            log_message(logging.ERROR, f"Error processing schedule {s}: {e}")
            continue

saved_schedules = load_schedule()
if saved_schedules:
    schedule_recognition(saved_schedules)

# -------------------------------------------------------------------
# Health Check
# -------------------------------------------------------------------
def monitor_speech_recognition():
    global is_recognizing, should_be_recognizing
    while True:
        try:
            if is_recognizing:
                log_message(logging.DEBUG, "Speech recognizer is active")
            elif should_be_recognizing:
                log_message(logging.WARNING, "Speech recognizer not active but should be; restarting")
                asyncio.run(start_recognition())
            else:
                log_message(logging.INFO, "Speech recognizer not active and not expected to be; skipping restart")
        except Exception as e:
            log_message(logging.ERROR, f"Health check failed: {e}")
        time.sleep(60)

health_thread = threading.Thread(target=monitor_speech_recognition, daemon=True)
health_thread.start()

# -------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------
def cleanup():
    try:
        vosk_recognizer.stop_recognition()
        log_message(logging.INFO, "Vosk speech recognition stopped during cleanup.")
    except Exception as e:
        log_message(logging.ERROR, f"Error stopping Vosk speech recognition during cleanup: {e}")

atexit.register(cleanup)

# -------------------------------------------------------------------
# Simulated Speech Input for Debugging
# -------------------------------------------------------------------
def simulate_speech_input(text):
    """Simulate speech input for testing"""
    on_vosk_recognizing(text)
    on_vosk_recognized(text)

if os.getenv("DEBUG_MODE"):
    simulate_speech_input("This is a test caption.")

# -------------------------------------------------------------------
# Unit Tests
# -------------------------------------------------------------------
class TestSpeechProcessing(unittest.TestCase):
    def test_spelling_corrections(self):
        self.assertEqual(spelling_corrections("genisis"), "Genesis")
        self.assertEqual(spelling_corrections("jesus christ"), "Jesus Christ")

    def test_bible_books(self):
        self.assertEqual(correct_bible_books("psalms 23"), "Psalms 23")
        self.assertEqual(correct_bible_books("hello world"), "hello world")

    def test_validate_time_format(self):
        self.assertTrue(validate_time_format("09:30"))
        self.assertTrue(validate_time_format("23:59"))
        self.assertTrue(validate_time_format("9:30"))
        self.assertFalse(validate_time_format("25:00"))
        self.assertFalse(validate_time_format("09:60"))
        self.assertFalse(validate_time_format("09:30:00"))
        self.assertFalse(validate_time_format(""))

@app.post("/clear_production_captions", dependencies=[Depends(get_current_username)])
async def clear_production_captions():
    global production_caption, production_caption_history, transcript, last_caption, user_caption, user_caption_history, user_last_text
    # Clear production view data
    production_caption = ""
    production_caption_history = ""
    transcript = []
    last_caption = ""
    
    # Clear user view data
    user_caption = ""
    user_caption_history = {lang: [] for lang in user_caption_history.keys()}
    user_last_text = {lang: "" for lang in user_last_text.keys()}
    
    # Send empty captions to clear both production and user views
    try:
        # Clear production view
        await send_caption_to_clients({"en-US": ""}, languages=["en-US"], caption_type="production")
        
        # Clear user view for all supported languages
        dictionary = load_dictionary()
        all_languages = [lang["code"] for lang in dictionary.get("supported_languages", [])]
        empty_user_captions = {lang: "" for lang in all_languages}
        await send_caption_to_clients(empty_user_captions, languages=all_languages, caption_type="user")
        
        log_message(logging.INFO, f"All captions cleared successfully for {len(all_languages)} languages")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to send clear captions: {e}")
    
    return {"status": "success", "message": "All captions cleared"}

@app.get("/user_settings", dependencies=[Depends(get_current_username)])
async def get_user_settings():
    return USER_SETTINGS

@app.post("/user_settings", dependencies=[Depends(get_current_username)])
async def set_user_settings(settings: dict):
    global USER_SETTINGS
    valid_settings = {k: v for k, v in settings.items() if k in DEFAULT_USER_SETTINGS}
    USER_SETTINGS.update(valid_settings)
    save_user_settings(USER_SETTINGS)
    log_message(logging.INFO, f"User settings updated via API: {valid_settings}")
    try:
        await broadcast_user_settings(valid_settings)
        log_message(logging.DEBUG, f"User settings broadcasted to {len(clients)} clients")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to broadcast user settings: {e}")
    return {"status": "success"}

# Unauthenticated endpoints for user view
@app.get("/user_settings_public")
async def get_user_settings_public():
    """Public endpoint for user view settings - no authentication required"""
    return USER_SETTINGS

@app.post("/user_settings_public")
async def set_user_settings_public(settings: dict):
    """Public endpoint for user view settings - no authentication required"""
    global USER_SETTINGS
    valid_settings = {k: v for k, v in settings.items() if k in DEFAULT_USER_SETTINGS}
    USER_SETTINGS.update(valid_settings)
    save_user_settings(USER_SETTINGS)
    log_message(logging.INFO, f"User settings updated via public API: {valid_settings}")
    try:
        await broadcast_user_settings(valid_settings)
        log_message(logging.DEBUG, f"User settings broadcasted to {len(clients)} clients")
    except Exception as e:
        log_message(logging.ERROR, f"Failed to broadcast user settings: {e}")
    return {"status": "success"}

async def broadcast_user_settings(settings):
    for client in clients:
        try:
            await client.send_text(json.dumps({"type": "user_settings", "settings": settings}))
            log_message(logging.DEBUG, f"Sent user settings to client: {client.client}")
        except Exception as e:
            log_message(logging.ERROR, f"WebSocket send error for user settings: {e}")
            clients.remove(client)

@app.get("/recognition_status", dependencies=[Depends(get_current_username)])
async def recognition_status():
    global is_recognizing
    return {"is_recognizing": is_recognizing}

@app.post("/set_user_language")
async def set_user_language(language_data: dict):
    global current_user_language
    language_code = language_data.get("language", "en-US")
    current_user_language = language_code
    log_message(logging.INFO, f"User language changed to: {language_code}")
    return {"status": "success", "current_language": current_user_language}

if __name__ == "__main__":
    if os.getenv("RUN_TESTS"):
        unittest.main()
    else:
        while True:
            time.sleep(1)