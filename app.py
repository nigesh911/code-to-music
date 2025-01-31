from flask import Flask, render_template, request, send_file, Response
import os
from slugify import slugify
import re
from music21 import stream, note, tempo, instrument, harmony, scale, pitch
import tempfile

app = Flask(__name__)

def analyze_code_complexity(code):
    num_functions = len(re.findall(r'def\s+\w+\s*\(', code))
    num_classes = len(re.findall(r'class\s+\w+\s*[:\(]', code))
    num_loops = len(re.findall(r'(for|while)\s+', code))
    num_conditionals = len(re.findall(r'if\s+', code))
    
    complexity = (num_functions * 2 + num_classes * 3 + num_loops + num_conditionals) / 10
    return min(max(complexity, 0.5), 2.0)

def get_scale_notes():
    major_scale = scale.MajorScale('C4')
    return [p.midi for p in major_scale.getPitches()]

def create_chord_progression():
    return ['C', 'F', 'G', 'Am']

def code_to_music(code_text):
    main_stream = stream.Stream()
    
    complexity = analyze_code_complexity(code_text)
    mm_mark = tempo.MetronomeMark(number=int(100 * complexity))  # Increased base tempo
    main_stream.append(mm_mark)
    
    scale_notes = get_scale_notes()
    
    melody_part = stream.Part()
    chord_part = stream.Part()
    
    melody_part.insert(0, instrument.Piano())
    chord_part.insert(0, instrument.Piano())
    
    # Process multiple characters at once
    chunk_size = 4
    lines = code_text.split('\n')
    current_time = 0
    chord_names = create_chord_progression()
    current_chord = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        indent = len(line) - len(line.lstrip())
        octave_shift = indent // 4
        
        chars = line.strip()
        for i in range(0, len(chars), chunk_size):
            chunk = chars[i:i+chunk_size]
            
            for char in chunk:
                ascii_val = ord(char)
                note_index = ascii_val % len(scale_notes)
                note_value = scale_notes[note_index]
                
                note_value += octave_shift * 12
                
                # Simplified duration logic
                n = note.Note(note_value, quarterLength=0.25)
                n.volume.velocity = 100 if char.isupper() else (80 if char.islower() else 60)
                
                melody_part.append(n)
                
            if current_time % 4 == 0:
                chord_name = chord_names[current_chord % len(chord_names)]
                chord_part.append(harmony.ChordSymbol(chord_name))
                current_chord += 1
                
            current_time += len(chunk)
    
    main_stream.append(melody_part)
    main_stream.append(chord_part)
    
    return main_stream

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    code = request.form.get('code', '')
    if not code:
        return 'No code provided', 400
    
    music_stream = code_to_music(code)
    
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        music_stream.write('midi', fp=tmp.name)
        tmp.close()  # Close the file before reading it
        
        with open(tmp.name, 'rb') as f:
            midi_data = f.read()
            
        response = Response(midi_data, mimetype='audio/midi')
        response.headers['Content-Disposition'] = f'attachment; filename=code_music_{slugify(code[:20])}.mid'
        return response
        
    except Exception as e:
        return f'Error generating MIDI file: {str(e)}', 500
        
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass  # Ignore errors during cleanup

app = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True) 