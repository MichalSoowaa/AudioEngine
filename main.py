from core.wav import load_wav, save_wav
from processing.pipeline import apply_chain
from effects import load_effects

if __name__ == "__main__":
    load_effects()

    audio = load_wav("samp1.wav")
    print(audio.num_channels, ' ', audio.sample_rate, ' ', audio.sample_width)

    chain = [
        #("volume", {"factor": 0.5}),
        ("normalize", {}),
        ("echo", {"delay_ms": 300, "decay": 1.0})
    ]

    processed = apply_chain(audio, chain, parallel = True)

    save_wav("samp1_output4.wav", processed)