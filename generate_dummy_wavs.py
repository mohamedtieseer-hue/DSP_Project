import numpy as np
import soundfile as sf
import os

def generate_tone(freq1, freq2, duration, fs=44100):
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # Stereo signal: distinct left and right
    left = 0.5 * np.sin(2 * np.pi * freq1 * t)
    right = 0.5 * np.sin(2 * np.pi * freq2 * t)
    return np.vstack((left, right)).T, fs

def create_dummies():
    # File 1: Low frequencies
    if not os.path.exists("Andrea_Bocelli_Besame_Mucho.wav"):
        print("Generating dummy Andrea_Bocelli_Besame_Mucho.wav...")
        data1, fs = generate_tone(440, 880, 5) # A4, A5
        sf.write("Andrea_Bocelli_Besame_Mucho.wav", data1, fs)
    
    # File 2: Higher frequencies
    if not os.path.exists("Zinda_Banda_Jawan.wav"):
        print("Generating dummy Zinda_Banda_Jawan.wav...")
        data2, fs = generate_tone(1200, 2400, 5) 
        sf.write("Zinda_Banda_Jawan.wav", data2, fs)

if __name__ == "__main__":
    create_dummies()
