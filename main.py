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