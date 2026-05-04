from tkinter import filedialog, messagebox
from core.wav import load_wav, save_wav
from processing.pipeline import apply_chain
from effects.registry import list_effects, get_effect_params
import tkinter as tk
import threading
import queue
import sounddevice as sd
import numpy as np


class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Editor")
        self.audio = None
        self.selected_effect = None
        self.queue = queue.Queue()
        self.param_widgets = {}
        self.build_ui()

    def build_ui(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=5)

        tk.Button(frame_top, text="Load", command=self.load_file).pack(side=tk.LEFT)
        tk.Button(frame_top, text="Save", command=self.save_file).pack(side=tk.LEFT)

        self.effects_frame = tk.Frame(self.root)
        self.effects_frame.pack()

        tk.Label(self.effects_frame, text="Effects").pack()

        for effect in list_effects():
            btn = tk.Button(self.effects_frame, text=effect, command=lambda e=effect: self.select_effect(e))
            btn.pack(fill="x")

        self.params_frame = tk.Frame(self.root)
        self.params_frame.pack()

        self.params_entries = {}

        self.apply_button = tk.Button(self.root, text="Apply effect", command=self.apply_effect)
        self.apply_button.pack()

        tk.Button(frame_top, text="Start", command=self.play_audio).pack(side=tk.LEFT)
        tk.Button(frame_top, text="Stop", command=self.stop_audio).pack(side=tk.LEFT)

        self.status = tk.Label(self.root, text="Ready")
        self.status.pack()

        self.canvas = tk.Canvas(self.root, width=800, height=200, bg="black")
        self.canvas.pack(pady=10)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])

        if not path:
            return

        self.audio = load_wav(path)
        self.draw_waveform()
        self.status.config(text=f"Loaded: {path}")

    def save_file(self):
        if not self.audio:
            return

        path = filedialog.asksaveasfilename(defaultextension=".wav")

        if not path:
            return

        save_wav(path, self.audio)
        self.status.config(text=f"Saved: {path}")

    def select_effect(self, effect):
        self.selected_effect = effect
        self.build_params(effect)

    def build_params(self, effect):
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        self.param_widgets.clear()

        params = get_effect_params(effect)

        for name, meta in params.items():
            frame = tk.Frame(self.params_frame)
            frame.pack(anchor="w", pady=2)
            label_text = name

            if not meta["has_default"]:
                label_text += " *"

            tk.Label(frame, text=label_text).pack(side=tk.LEFT)

            param_type = meta["type"]
            default = meta["default"]

            if param_type == bool:
                var = tk.BooleanVar(value=bool(default) if default is not None else False)
                widget = tk.Checkbutton(frame, variable=var)
                widget.pack(side=tk.LEFT)

            else:
                var = tk.StringVar()

                if default is not None:
                    var.set(str(default))

                widget = tk.Entry(frame, textvariable=var)
                widget.pack(side=tk.LEFT)

            self.param_widgets[name] = (widget, var, meta)

    def apply_effect(self):
        if not self.audio:
            messagebox.showerror("Error", "No audio loaded")
            return

        if not self.selected_effect:
            messagebox.showerror("Error", "No effect selected")
            return

        params = {}

        try:
            for name, (widget, var, meta) in self.param_widgets.items():
                raw_value = var.get()

                if raw_value == "":
                    if not meta["has_default"]:
                        raise ValueError(f"Parameter '{name}' is required")
                    continue

                param_type = meta["type"]

                if param_type == int:
                    value = int(raw_value)
                elif param_type == float:
                    value = float(raw_value)
                elif param_type == bool:
                    value = raw_value

                params[name] = value

        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        self.status.config(text="Processing...")

        chain = [(self.selected_effect, params)]
        #self.audio = apply_chain(self.audio, chain, parallel=True)
        thread = threading.Thread(
            target = self.process_audio,
            args = (self.audio, chain),
            daemon = True
        )
        self.apply_button.config(state="disabled")
        thread.start()

        self.root.after(100, self.check_queue)

    def process_audio(self, audio, chain):
        try:
            result = apply_chain(audio, chain, parallel=True)
            self.queue.put(("success", result))
        except Exception as e:
            self.queue.put(("error", str(e)))

    def check_queue(self):
        try:
            status, data = self.queue.get_nowait()

            if status == "success":
                self.audio = data
                self.draw_waveform()
                self.status.config(text="Done")
                self.apply_button.config(state="normal")
            elif status == "error":
                self.status.config(text="Error")
                messagebox.showerror("Error", data)
        except queue.Empty:
            self.root.after(100, self.check_queue)

    def draw_waveform(self):
        self.canvas.delete("all")

        if not self.audio or not self.audio.samples:
            return

        samples = self.audio.samples
        channels = self.audio.num_channels

        width = int(self.canvas["width"])
        height = int(self.canvas["height"])
        mid_y = height // 2
        step = max(1, len(samples) // width)

        def get_sample(i, channel):
            index = i * channels + channel

            if index >= len(samples):
                return 0

            return samples[index]

        for x in range(width):
            i = x * step

            if channels == 1:
                sample = samples[i] if i < len(samples) else 0

                # normalize (-32768..32767 -> -1..1)
                norm = sample / 32768

                y = int(mid_y - norm * mid_y)

                self.canvas.create_line(x, mid_y, x, y, fill="lime")
            else:
                left = get_sample(i, 0)
                norm_l = left / 32768
                y_l = int((mid_y // 2) - norm_l * (mid_y // 2))

                self.canvas.create_line(x, mid_y // 2, x, y_l, fill="cyan")

                right = get_sample(i, 1)
                norm_r = right / 32768
                base = mid_y + (mid_y // 2)
                y_r = int(base - norm_r * (mid_y // 2))

                self.canvas.create_line(x, base, x, y_r, fill="orange")

    def audio_to_numpy(self):
        samples = self.audio.samples
        channels = self.audio.num_channels
        arr = np.array(samples, dtype=np.int16)

        if channels == 1:
            return arr

        return arr.reshape(-1, channels)

    def play_audio(self):
        if not self.audio:
            return

        data = self.audio_to_numpy()
        data = data.astype(np.float32) / 32768.0

        sd.play(data, samplerate=self.audio.sample_rate)

    def stop_audio(self):
        sd.stop()