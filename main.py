from core.wav import load_wav, save_wav

if __name__ == "__main__":
    audio = load_wav("samp1.wav")
    save_wav("samp1_output.wav", audio)