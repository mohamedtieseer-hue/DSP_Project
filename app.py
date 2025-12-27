import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import dsp
import soundfile as sf
import os

st.set_page_config(page_title="DSP Audio Project", layout="wide")

st.title("DSP End-to-End Project: FDM & Filtering")
st.markdown("""
This application processes two stereo wav files (4 channels total), applies filters, 
modulates them to different carrier frequencies (FDM), combines them, and then recovers them.
""")

# --- Sidebar / Setup ---
st.sidebar.header("Configuration")

# File Selection (Auto-detect or Upload could be added, here we stick to assignment default)
file1 = "Andrea_Bocelli_Besame_Mucho.wav"
file2 = "Zinda_Banda_Jawan.wav"

if not os.path.exists(file1) or not os.path.exists(file2):
    st.error("Input files not found! Please ensure input WAVs are in the root directory.")
    st.stop()

# Ordering
st.subheader("Channel Input Mapping")
st.write("Original Channels: 1 (File1-L), 2 (File1-R), 3 (File2-L), 4 (File2-R)")

# Permutation Interface
col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)

# Helper to enforce uniqueness roughly (basic UI)
options = [1, 2, 3, 4]
with col_sel1:
    o1 = st.selectbox("Slot 1 Channel", options, index=0)
with col_sel2:
    o2 = st.selectbox("Slot 2 Channel", options, index=1)
with col_sel3:
    o3 = st.selectbox("Slot 3 Channel", options, index=2)
with col_sel4:
    o4 = st.selectbox("Slot 4 Channel", options, index=3)

selected_order = [o1, o2, o3, o4]

if len(set(selected_order)) != 4:
    st.error("⚠️ Please select 4 UNIQUE channels (permutation of 1,2,3,4)!")
    st.stop()

# --- processing ---
if 'processed_data' not in st.session_state:
    st.session_state['processed_data'] = None

if st.button("RUN DSP PIPELINE"):
    with st.spinner("Processing Audio... (Loading -> Filtering -> Upsampling -> Modulating -> Demodulating)"):
        # 1. Load
        raw_channels, orig_fs = dsp.load_and_prep_data(file1, file2)
        
        # 2. Reorder per user selection (Indices are 0-based, options are 1-based)
        ordered_channels = [raw_channels[i-1] for i in selected_order]
        
        # 3. Filter
        filtered, filt_desc = dsp.design_and_apply_filters(ordered_channels, orig_fs)
        
        # 4. Modulate
        composite, carriers, mod_fs, upsampled_chans = dsp.modulation_process(filtered, orig_fs)
        
        # 5. Demodulate
        recovered = dsp.demodulation_process(composite, carriers, mod_fs, orig_fs)
        
        # Store in session
        st.session_state['processed_data'] = {
            'channels': ordered_channels,  # Raw reordered
            'filtered': filtered,
            'filt_desc': filt_desc,
            'composite': composite,
            'recovered': recovered,
            'carriers': carriers,
            'orig_fs': orig_fs,
            'mod_fs': mod_fs,
            'upsampled_chans': upsampled_chans # for checking pre-mod spectrum
        }
        st.success("Processing Complete!")

# --- Visualization ---

if st.session_state['processed_data']:
    data = st.session_state['processed_data']
    fs = data['orig_fs']
    mod_fs = data['mod_fs']
    
    # OUTPUT FOLDER
    os.makedirs("outputs", exist_ok=True)
    
    st.divider()
    
    # 1. Filtered Channels (Pre-Modulation)
    st.header("1. Filtered Channels - Frequency Domain")
    
    fig1, axs1 = plt.subplots(2, 2, figsize=(12, 8))
    axs1 = axs1.flatten()
    
    for i in range(4):
        # Use the upsampled version for plotting to match the freq axis scale of carriers conceptually, 
        # or just original. Original is better to see the filter effect in baseband.
        f, mag = dsp.compute_spectrum(data['filtered'][i], fs)
        axs1[i].plot(f, mag, color='tab:blue')
        axs1[i].set_title(f"Channel {selected_order[i]} - {data['filt_desc'][i]}\n(Selected Slot {i+1})")
        axs1[i].set_xlabel("Freq (Hz)")
        axs1[i].set_ylabel("Magnitude")
        axs1[i].grid(True, alpha=0.3)
        
        # Audio Player
        col_a, col_b = st.columns([1, 4])
        st.markdown(f"**Slot {i+1} Filtered Audio:**")
        st.audio(data['filtered'][i], sample_rate=fs)
        
    st.pyplot(fig1)
    
    st.divider()
    
    # 2. Composite Signal
    st.header("2. Composite Signal (FDM Output)")
    st.write(f"Modulation Fs: {mod_fs} Hz. Carriers: {data['carriers']} Hz")
    
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    f_comp, mag_comp = dsp.compute_spectrum(data['composite'], mod_fs)
    ax2.plot(f_comp, mag_comp, color='tab:red')
    ax2.set_title("Composite Signal Spectrum")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.grid(True)
    
    # Annotate carriers
    for c in data['carriers']:
        ax2.axvline(x=c, color='k', linestyle='--', alpha=0.5)
        ax2.text(c, max(mag_comp)*0.8, f"{c/1000}k", rotation=90)
        
    st.pyplot(fig2)
    
    st.audio(data['composite'], sample_rate=mod_fs)
    # Save button
    path_composite = "outputs/composite_signal.wav"
    sf.write(path_composite, data['composite'], mod_fs)
    st.download_button("Download Composite WAV", open(path_composite, "rb"), "composite_signal.wav")
    
    st.divider()
    
    # 3. Recovered Channels
    st.header("3. Recovered Channels (Demodulated)")
    
    fig3, axs3 = plt.subplots(2, 2, figsize=(12, 8))
    axs3 = axs3.flatten()
    
    for i in range(4):
        f, mag = dsp.compute_spectrum(data['recovered'][i], fs)
        axs3[i].plot(f, mag, color='tab:green')
        axs3[i].set_title(f"Recovered Ch {selected_order[i]} (from Carrier {data['carriers'][i]}Hz)")
        axs3[i].set_xlabel("Freq (Hz)")
        axs3[i].grid(True)
        
        st.markdown(f"**Slot {i+1} Recovered:**")
        st.audio(data['recovered'][i], sample_rate=fs)
        
        # Save
        path_rec = f"outputs/recovered_ch_{selected_order[i]}.wav"
        sf.write(path_rec, data['recovered'][i], fs)

    st.pyplot(fig3)
    
else:
    st.info("Click 'RUN DSP PIPELINE' to start.")

st.markdown("---")
st.markdown("### Instructions")
st.markdown("1. Select channel order. 2. Run Pipeline. 3. View plots & play audio.")
