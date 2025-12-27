import numpy as np
import scipy.signal as signal
import soundfile as sf
import collections

# Channel container
Channel = collections.namedtuple('Channel', ['data', 'name', 'original_fs'])

def load_and_prep_data(file1_path, file2_path, target_fs=44100):
    """
    Loads two stereo wav files, resamples them to target_fs, 
    trims to min length, and separates into 4 channels.
    """
    # Load files
    y1, fs1 = sf.read(file1_path)
    y2, fs2 = sf.read(file2_path)
    
    # Resample if needed
    if fs1 != target_fs:
        num_samples = int(len(y1) * target_fs / fs1)
        y1 = signal.resample(y1, num_samples)
    if fs2 != target_fs:
        num_samples = int(len(y2) * target_fs / fs2)
        y2 = signal.resample(y2, num_samples)
        
    # Trim to match lengths
    min_len = min(len(y1), len(y2))
    y1 = y1[:min_len]
    y2 = y2[:min_len]
    
    # Normalize inputs standardly to avoid initial massive volume differences
    y1 = y1 / np.max(np.abs(y1)) if np.max(np.abs(y1)) > 0 else y1
    y2 = y2 / np.max(np.abs(y2)) if np.max(np.abs(y2)) > 0 else y2
    
    # Split into 4 channels
    # Ch1: File1 L, Ch2: File1 R, Ch3: File2 L, Ch4: File2 R
    channels = [
        y1[:, 0], # Ch1
        y1[:, 1], # Ch2
        y2[:, 0], # Ch3
        y2[:, 1]  # Ch4
    ]
    
    return channels, target_fs

def design_and_apply_filters(channels, fs):
    """
    Applies 4 different stable IIR filters (Butterworth).
    Returns filtered channels and filter descriptions.
    """
    filtered_channels = []
    filter_specs = []
    
    # Nyquist
    nyq = 0.5 * fs
    
    # Filter 1: Lowpass < 2000 Hz (Bass/Speech fund.)
    sos1 = signal.butter(4, 2000 / nyq, btype='low', output='sos')
    filt1 = signal.sosfilt(sos1, channels[0])
    filtered_channels.append(filt1)
    filter_specs.append("Lowpass (fc=2kHz): Isolates low freq components")

    # Filter 2: Bandpass 2000-5000 Hz (Mid-range/Vocals)
    sos2 = signal.butter(4, [2000 / nyq, 5000 / nyq], btype='band', output='sos')
    filt2 = signal.sosfilt(sos2, channels[1])
    filtered_channels.append(filt2)
    filter_specs.append("Bandpass (2-5kHz): Captures vocal/mid range")

    # Filter 3: Bandpass 5000-10000 Hz (Presence/High-mids)
    sos3 = signal.butter(4, [5000 / nyq, 10000 / nyq], btype='band', output='sos')
    filt3 = signal.sosfilt(sos3, channels[2])
    filtered_channels.append(filt3)
    filter_specs.append("Bandpass (5-10kHz): High-mid presence")

    # Filter 4: Highpass > 10000 Hz (Brilliance/Air)
    sos4 = signal.butter(4, 10000 / nyq, btype='high', output='sos')
    filt4 = signal.sosfilt(sos4, channels[3])
    filtered_channels.append(filt4)
    filter_specs.append("Highpass (fc=10kHz): High frequency detail")
    
    return filtered_channels, filter_specs

def compute_spectrum(signal_data, fs):
    """Computes single-sided magnitude spectrum."""
    n = len(signal_data)
    fft_data = np.fft.fft(signal_data)
    freqs = np.fft.fftfreq(n, d=1/fs)
    
    # Take positive half
    half_n = n // 2
    mag = np.abs(fft_data[:half_n]) / n # Normalize
    f = freqs[:half_n]
    
    return f, mag

def modulation_process(filtered_channels, fs):
    """
    Modulates each channel onto a carrier.
    Carrier spacing must accommodate the channel bandwidth.
    Our channels roughly occupy 0-2k, 2-5k, 5-10k, 10k+.
    Wait, if we filter them, they are band-limited (mostly).
    But FDM requires shifting them to non-overlapping bands.
    
    Let's pick carriers intelligently.
    Baseband is typically viewed as centered at 0 or near DC. 
    Our filtered signals are Real signals, so they have +/- frequency content.
    
    Standard AM-DSB-SC: x(t) * cos(2*pi*fc*t).
    Shifted visual: Center of frequency content shifts to fc.
    
    Given the filters:
    Ch1 (0-2k) -> Carrier 10k -> ends up at 8-12k.
    Ch2 (2-5k) -> Carrier 20k -> 15-25k.
    Ch3 (5-10k) -> Carrier 35k -> 25-45k.
    Ch4 (>10k) -> This one is tricky. It's highpass. 
    However, for FDM to work well, usually we start with baseband signals.
    The assignment asks to "Apply DIFFERENT filtering... then Modulate".
    If I take a Highpass signal (>10k) and modulate it by say 50k, it will have components at 50k +/- content.
    Content is 10k to 22k (Nyquist). 
    So 50k+10k=60k (aliasing!) if fs=44.1k is not handled.
    
    CRITICAL: The prompt implies FDM transmission simulation. 
    Usually we upsample (interpolate) to a much higher transmission rate to fit all carriers without aliasing.
    Target Fs for composite signal should probably be higher than 44.1kHz if we want to stack them purely.
    OR, we assume the "FDM" is just shifting them within the available audible bandwidth (0-22kHz) which is very tight for 4 channels.
    
    Let's try to fit them in 0-22kHz if possible, or decide to Upsample.
    Prompt: "Read both... verify sample rates". Doesn't say "Upsample for TX".
    But "Carriers must create NON-OVERLAPPING frequency bands".
    
    Let's assume we Upsample the composite logic to ensure quality, or just use a higher Fs internally.
    Let's pick an internal processing Fs = 4 * 44100 = 176400 Hz. This gives us bandwidth up to ~88kHz.
    Then we can easily stack 4 channels.
    
    Strategy:
    1. Upsample all filtered channels to Fs_high = 192000 Hz (standard high quality).
    2. Modulate with carriers:
       Ch1 (Effective BW ~2k) -> fc=10k (Band 8-12k)
       Ch2 (Effective BW ~3k) -> fc=20k (Band 17-23k)
       Ch3 (Effective BW ~5k) -> fc=35k (Band 30-40k)
       Ch4 (Effective BW ~10k) -> fc=60k (Band 50-70k)
    3. Sum.
    4. Demodulate: Bandpass at target, Mult by fc, Lowpass.
    5. Downsample back to 44.1kHz for playback.
    """
    
    # Upsample configuration
    fs_high = 192000
    carriers = [10000, 25000, 45000, 70000] # Separated bands
    
    modulated_signals = []
    
    # We need to upsample first
    upsampled_channels = []
    for sig in filtered_channels:
        num_resampled = int(len(sig) * fs_high / fs)
        # Using simple resample (FFT based) or linear. FFT based is fine for offline.
        sig_up = signal.resample(sig, num_resampled)
        upsampled_channels.append(sig_up)
    
    t = np.arange(len(upsampled_channels[0])) / fs_high
    
    for i, sig_up in enumerate(upsampled_channels):
        fc = carriers[i]
        mod = sig_up * np.cos(2 * np.pi * fc * t)
        modulated_signals.append(mod)
        
    composite = np.sum(modulated_signals, axis=0)
    
    # Normalize composite to prevent clipping
    composite = composite / np.max(np.abs(composite))
    
    return composite, carriers, fs_high, upsampled_channels

def demodulation_process(composite, carriers, fs_high, original_fs):
    """
    Recovers the signals.
    1. Bandpass around Carrier.
    2. Sync Demod (Mult by carrier).
    3. Lowpass filter to remove 2*fc component.
    4. Downsample.
    """
    recovered_channels = []
    t = np.arange(len(composite)) / fs_high
    nyq = 0.5 * fs_high
    
    # Estimated Bandwidths for filter design (approximate generous masks)
    # Ch1 (orig ~2k) -> at fc=10k, band is 8-12k. BW=4k.
    # We used specific carriers, let's design BPFs around them +/- bandwidth
    bw_estimates = [4000, 6000, 10000, 15000] # Half-widths roughly
    
    for i, fc in enumerate(carriers):
        # 1. Bandpass Isolation
        # Determine passband
        bw = bw_estimates[i]
        low = fc - bw
        high = fc + bw
        if low < 100: low = 100
        if high > nyq - 100: high = nyq - 100
        
        sos_bp = signal.butter(4, [low/nyq, high/nyq], btype='band', output='sos')
        isolated = signal.sosfilt(sos_bp, composite)
        
        # 2. Downconversion
        demod = isolated * np.cos(2 * np.pi * fc * t) * 2 # *2 to recover amplitude
        
        # 3. LPF to remove double freq term and get baseband
        # Cutoff should be roughly the original bandwidth of that channel
        # Ch1: 2k, Ch2: 5k, Ch3: 10k, Ch4: 12k
        lpf_cutoffs = [2500, 5500, 10500, 15000] 
        sos_lp = signal.butter(4, lpf_cutoffs[i]/nyq, btype='low', output='sos')
        baseband = signal.sosfilt(sos_lp, demod)
        
        # 4. Downsample
        num_original = int(len(baseband) * original_fs / fs_high)
        recovered = signal.resample(baseband, num_original)
        
        # Normalize
        rec_norm = recovered / np.max(np.abs(recovered))
        recovered_channels.append(rec_norm)
        
    return recovered_channels

