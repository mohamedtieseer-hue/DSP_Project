# DSP End-to-End Project

A comprehensive Python Digital Signal Processing project demonstrating FDM (Frequency Division Multiplexing), Audio Filtering, and Modulation/Demodulation within a Streamlit GUI.

## Project Structure

- `app.py`: Main Streamlit application entry point.
- `dsp.py`: Core signal processing logic module.
- `requirements.txt`: Python dependencies.
- `report.md`: Detailed DSP design report.
- `Andrea_Bocelli_Besame_Mucho.wav` / `Zinda_Banda_Jawan.wav`: Input files.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

## Features

- **Input Handling**: Robustly handles stereo wav files, correcting sample rate mismatches and trimming lengths.
- **Filtering**: Applies 4 distinct filters (Lowpass, Bandpass x2, Highpass) to separate audio features.
- **FDM Modulation**: Upsamples signals to 192kHz and modulates them onto Non-Overlapping carriers (10k, 25k, 45k, 70k Hz).
- **Visualization**: Real-time frequency spectrum plots for filtered, composite, and recovered signals.
- **Playback**: Integrated audio player for all stages.
- **Export**: Auto-saves outputs to `/outputs` folder.
