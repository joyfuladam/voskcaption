# Caption5 Application

A real-time captioning application with web interface and audio processing capabilities.

**✅ Successfully connected to GitHub at: https://github.com/joyfuladam/caption.git**

## Features

- Real-time audio transcription
- Web-based dashboard interface
- User management and settings
- Dictionary customization
- Scheduled operations

## Development Workflow

### For Developers (Making Updates)

1. **Make your changes** to the application files
2. **Stage your changes**:
   ```bash
   git add .
   ```
3. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "Description of your changes"
   ```
4. **Push to remote repository**:
   ```bash
   git push origin main
   ```

### For Users (Getting Updates)

1. **Navigate to your local copy** of the application
2. **Pull the latest changes**:
   ```bash
   git pull origin main
   ```
3. **Restart the application** if necessary

## Setup Instructions

### First Time Setup

1. Clone the repository:
   ```bash
   git clone [REPOSITORY_URL]
   cd caption5
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python captionStable.py
   ```

### Updating the Application

Use the provided update script:
```bash
./update_app.sh
```

## File Structure

- `captionStable.py` - Main application file
- `dashboard.html` - Main web interface
- `requirements.txt` - Python dependencies
- `config.json` - Application configuration
- `user_settings.json` - User preferences
- `dictionary.json` - Custom dictionary entries

## Requirements

- Python 3.8+
- See `requirements.txt` for specific package versions

## License

[Add your license information here]
