from flask import Flask
from flask import send_from_directory
from flask import request
from flask import jsonify
from flask_cors import CORS  # Import CORS
import librosa
import numpy as np
import noisereduce as nr
import scipy.signal
import pretty_midi
from midi2audio import FluidSynth
import os

app = Flask(__name__)
cors = CORS(app)  # Enable CORS for all routes

@app.route('/process-audio', methods=['POST'])
def process_audio():
    file = request.files['audio']
    file_path = "sampleRecording1.mp3"
    file.save(file_path)

    # Processing functions
    def pitch_to_note_and_duration(pitch, duration):
        A4 = 440.0
        C0 = A4 * 2**(-4.75)
        if pitch == 0:
            return 'Rest', duration
        h = round(8 * np.log2(pitch / C0))
        octave = h // 8
        n = h % 8
        note = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C'][n]
        return f"{note}{octave}", duration

    def detect_pitch(audio_file):
        y, sr = librosa.load(audio_file)
        y = nr.reduce_noise(y=y, sr=sr)
        pitches, magnitudes = librosa.core.piptrack(y=y, sr=sr)
        frame_duration = librosa.frames_to_time(1, sr=sr)

        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)

        pitch_values = scipy.signal.medfilt(pitch_values, kernel_size=5)
        aggregated_pitches = []
        last_pitch = None
        for pitch in pitch_values:
            if last_pitch is None or abs(pitch - last_pitch) > 1:
                aggregated_pitches.append(pitch)
                last_pitch = pitch

        return aggregated_pitches, frame_duration

    def convert_pitches_to_notes(pitch_values, frame_duration, min_duration=0.5):
        notes = []
        last_note = None
        duration = 0
        for pitch in pitch_values:
            note, note_duration = pitch_to_note_and_duration(pitch, frame_duration)
            if note != last_note:
                if last_note is not None:
                    notes.append((last_note, max(duration, min_duration)))
                last_note = note
                duration = frame_duration
            else:
                duration += frame_duration
        if last_note is not None:
            notes.append((last_note, max(duration, min_duration)))
        return notes

    def save_notes_to_midi(notes, file_name, tempo_bpm=120):
        midi = pretty_midi.PrettyMIDI(initial_tempo=tempo_bpm)
        piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
        piano = pretty_midi.Instrument(program=piano_program)

        start_time = 0
        for note_name, duration in notes:
            if note_name != 'Rest':
                note_number = pretty_midi.note_name_to_number(note_name)
                note = pretty_midi.Note(
                    velocity=100, pitch=note_number, start=start_time, end=start_time + duration)
                piano.notes.append(note)
            start_time += duration

        midi.instruments.append(piano)
        midi.write(file_name)

    def convert_midi_to_mp3(midi_file, mp3_file, sound_font='piano.sf2'):
        fs = FluidSynth(sound_font)
        fs.midi_to_audio(midi_file, mp3_file)

    # Process audio
    pitches, frame_duration = detect_pitch(file_path)
    notes = convert_pitches_to_notes(pitches, frame_duration)
    midi_file = "output_music.mid"
    save_notes_to_midi(notes, midi_file)
    mp3_file = "output_music.mp3"
    convert_midi_to_mp3(midi_file, mp3_file)

    return jsonify({'mp3_url': '/download/output_music.mp3'})

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(port=5000)
