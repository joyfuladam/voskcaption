#!/bin/bash
# Audio Preparation Script for Vosk Training

echo "🎵 Preparing audio data for Vosk training..."

# Convert audio to required format (16kHz, mono, WAV)
for file in training_data/audio/*.{wav,mp3,m4a,flac,aac}; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        name="${filename%.*}"
        echo "Converting: $filename"
        
        # Convert to 16kHz mono WAV
        ffmpeg -i "$file" -ar 16000 -ac 1 -f wav "training_data/processed/${name}.wav"
        
        # Normalize audio levels
        sox "training_data/processed/${name}.wav" "training_data/processed/${name}_normalized.wav" norm
        
        # Remove silence
        sox "training_data/processed/${name}_normalized.wav" "training_data/processed/${name}_final.wav" silence 1 0.1 1% -1 0.1 1%
        
        echo "✅ Processed: ${name}_final.wav"
    fi
done

echo "🎉 Audio preparation complete!"
