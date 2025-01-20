from flask import Flask, render_template, request, send_file
import os
from slugify import slugify
import re
from music21 import stream, note, tempo, instrument, harmony, scale, pitch

app = Flask(__name__)

def analyze_code_complexity(code):
    # Analyze code patterns
    num_functions = len(re.findall(r'def\s+\w+\s*\(', code))
    num_classes = len(re.findall(r'class\s+\w+\s*[:\(]', code))
    num_loops = len(re.findall(r'(for|while)\s+', code))
    num_conditionals = len(re.findall(r'if\s+', code))
    
    complexity = (num_functions * 2 + num_classes * 3 + num_loops + num_conditionals) / 10
    return min(max(complexity, 0.5), 2.0)

def get_scale_notes():
    # Use C major pentatonic scale for a more pleasant sound
    major_scale = scale.MajorScale('C4')
    return [p.midi for p in major_scale.getPitches()]

def create_chord_progression():
    # Create a simple chord progression (I-IV-V-vi)
    return ['C', 'F', 'G', 'Am']  # Just return the chord names

def code_to_music(code_text):
    # Create a music21 stream
    main_stream = stream.Stream()
    
    # Set tempo based on code complexity
    complexity = analyze_code_complexity(code_text)
    mm_mark = tempo.MetronomeMark(number=int(80 * complexity))
    main_stream.append(mm_mark)
    
    # Get available notes from scale
    scale_notes = get_scale_notes()
    
    # Create melody part
    melody_part = stream.Part()
    chord_part = stream.Part()
    
    # Add instrument
    melody_part.insert(0, instrument.Piano())
    chord_part.insert(0, instrument.Piano())
    
    # Process code into musical elements
    lines = code_text.split('\n')
    current_time = 0
    chord_names = create_chord_progression()
    current_chord = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        # Calculate indentation for octave shifts
        indent = len(line) - len(line.lstrip())
        octave_shift = indent // 4
        
        # Process each character in the line
        for char in line.strip():
            # Map character to note
            ascii_val = ord(char)
            note_index = ascii_val % len(scale_notes)
            note_value = scale_notes[note_index]
            
            # Adjust for indentation
            note_value += octave_shift * 12
            
            # Create note
            duration_value = 'eighth'
            if char.isupper():
                duration_value = 'quarter'
            elif char.isdigit():
                duration_value = 'sixteenth'
                
            # Create and add note to melody
            n = note.Note(note_value, quarterLength=0.5)
            if char.isupper():
                n.volume.velocity = 100
            elif char.islower():
                n.volume.velocity = 80
            else:
                n.volume.velocity = 60
                
            melody_part.append(n)
            
            # Add chord every 4 notes
            if current_time % 4 == 0:
                # Create a new chord object each time
                chord_name = chord_names[current_chord % len(chord_names)]
                chord_part.append(harmony.ChordSymbol(chord_name))
                current_chord += 1
                
            current_time += 1
    
    # Add parts to main stream
    main_stream.append(melody_part)
    main_stream.append(chord_part)
    
    # Export to MIDI
    return main_stream

def stream_to_midi_file(music_stream, filepath):
    music_stream.write('midi', fp=filepath)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    code = request.form.get('code', '')
    if not code:
        return 'No code provided', 400
    
    # Generate music
    music_stream = code_to_music(code)
    
    # Create a filename based on first few characters of code
    filename = f"code_music_{slugify(code[:20])}.mid"
    
    # Ensure 'midi_files' directory exists
    os.makedirs('midi_files', exist_ok=True)
    filepath = os.path.join('midi_files', filename)
    
    # Save the MIDI file
    stream_to_midi_file(music_stream, filepath)
    
    # Send file to user
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='audio/midi'
    )

if __name__ == '__main__':
    app.run(debug=True) 