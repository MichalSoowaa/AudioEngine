from tkinter import filedialog, messagebox
from core.wav import load_wav, save_wav
from processing.pipeline import apply_chain
from effects.registry import list_effects, get_effect_params
import tkinter as tk
import threading
import queue
import sounddevice as sd
import numpy as np
import time


class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Editor")
        self.audio = None
        self.selected_effect = None
        self.param_widgets = {}

        self.playing = False
        self.paused = False
        self.play_start_time = 0
        self.pause_time = 0
        self.play_obj = None

        self.queue = queue.Queue()

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

        self.apply_button = tk.Button(self.root, text="Apply effect", command=self.apply_effect)
        self.apply_button.pack()

        self.play_button = (tk.Button(frame_top, text="Play", command=self.play_audio))
        self.play_button.pack(side=tk.LEFT)

        tk.Button(frame_top, text="Stop", command=self.stop_audio).pack(side=tk.LEFT)

        tk.Button(frame_top, text="Resume", command=self.resume_audio).pack(side=tk.LEFT)
        tk.Button(frame_top, text="Pause", command=self.pause_audio).pack(side=tk.LEFT)

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
        self.play_button.config(state="normal")

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
                self.apply_button.config(state="normal")
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
        step = max(1, len(samples) // width // 2)

        def get_sample(i, channel):
            index = i * channels + channel

            if index >= len(samples):
                return 0

            return samples[index]

        for x in range(width):
            i = x * step

            if channels == 1:
                sample = samples[i] if i < len(samples) else 0

                y = int(mid_y - sample * mid_y)

                self.canvas.create_line(x, mid_y, x, y, fill="lime", tags="waveform")
            else:
                left = get_sample(i, 0)
                y_l = int((mid_y // 2) - left * (mid_y // 2))

                self.canvas.create_line(x, mid_y // 2, x, y_l, fill="cyan", tags="waveform")

                right = get_sample(i, 1)
                base = mid_y + (mid_y // 2)
                y_r = int(base - right * (mid_y // 2))

                self.canvas.create_line(x, base, x, y_r, fill="orange", tags="waveform")

    def audio_to_numpy(self):
        arr = np.array(self.audio.samples, dtype=np.float32)

        if self.audio.num_channels == 1:
            return arr

        return arr.reshape(-1, self.audio.num_channels)

    def play_audio(self):
        if not self.audio:
            return

        data = self.audio_to_numpy()
        data = data.astype(np.float32)

        self.playing = True
        self.paused = False
        self.play_start_time = time.time()

        sd.play(data, samplerate=self.audio.sample_rate)
        self.update_cursor()

    def stop_audio(self):
        sd.stop()
        self.playing = False
        self.paused = False

    def pause_audio(self):
        if not self.playing or self.paused:
            return

        latency = sd.query_devices(sd.default.device['output'], 'output')['default_low_output_latency']

        sd.stop()
        self.paused = True
        self.pause_time = time.time() - latency

    def resume_audio(self):
        if not self.paused:
            return

        elapsed = self.pause_time - self.play_start_time

        data = self.audio_to_numpy()
        data = data.astype(np.float32)

        start_sample = int(elapsed * self.audio.sample_rate)
        sliced = data[start_sample:]

        sd.play(sliced, samplerate=self.audio.sample_rate)
        self.play_start_time = time.time() - elapsed
        self.paused = False

        self.update_cursor()

    def update_cursor(self):
        if not self.playing or self.paused:
            return

        elapsed = time.time() - self.play_start_time
        total_duration = len(self.audio.samples) / self.audio.sample_rate / self.audio.num_channels
        progress = min(1.0, elapsed / total_duration)

        width = int(self.canvas["width"])
        x = int(progress * width)

        self.canvas.delete("cursor")
        self.canvas.create_line(x, 0, x, int(self.canvas["height"]), fill="red", tags="cursor")

        if progress < 1.0:
            self.root.after(30, self.update_cursor)
        else:
            self.playing = False
            self.play_start_time = 0
            self.pause_time = 0