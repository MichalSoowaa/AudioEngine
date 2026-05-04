from effects import load_effects
from ui.app import AudioApp
from multiprocessing import freeze_support
import tkinter as tk

if __name__ == "__main__":
    freeze_support()

    load_effects()

    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()



    # audio = load_wav("samp1.wav")
    # print(audio.num_channels, ' ', audio.sample_rate, ' ', audio.sample_width)
    #
    # chain = [
    #     #("volume", {"factor": 0.5}),
    #     ("normalize", {}),
    #     ("echo", {"delay_ms": 300, "decay": 1.0})
    # ]
    #
    # processed = apply_chain(audio, chain, parallel = True)
    #
    # save_wav("samp1_output4.wav", processed)