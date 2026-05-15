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
        self.root.title("Audio Processor")
        self.audio = None
        self.audio_data = None
        self.param_widgets = {}

        self.playing = False
        self.paused = False
        self.play_start_time = 0
        self.pause_time = 0
        self.play_obj = None

        self.queue = queue.Queue()

        self.build_ui()

    def build_ui(self):
        top_bar = tk.Frame(self.root)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.columnconfigure(1, weight=1)

        left_controls = tk.Frame(top_bar)
        left_controls.grid(row=0, column=0, sticky="w")
        tk.Button(left_controls, text="Load", command=self.load_file).pack(side=tk.LEFT)
        tk.Button(left_controls, text="Save", command=self.save_file).pack(side=tk.LEFT)
        effects_button = tk.Menubutton(top_bar, text="Effects ▼")
        effects_menu = tk.Menu(effects_button, tearoff=False)
        effects_button.config(menu=effects_menu)
        effects_button.grid(row=0, column=2)

        for effect_name in list_effects():
            effects_menu.add_command(label=effect_name, command=lambda e=effect_name: self.open_effect_dialog(e))

        transport_bar = tk.Frame(self.root)
        transport_bar.grid(row=1, column=0, pady=5)
        self.play_pause_button = (tk.Button(transport_bar, text="▶ Play", width=12, command=self.toggle_play_pause))
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = tk.Button(transport_bar, text="■ Stop", width=12, command=self.stop_audio, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.grid(row=4, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var, anchor="w")
        self.status_label.pack(fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=800, height=300, bg="black")
        self.canvas.grid(row=2, column=0, sticky="nsew")

        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])

        if not path:
            return

        self.audio = load_wav(path)
        self.rebuild_cache()
        self.draw_waveform()
        self.status_var.set(f"Loaded: {path} | {self.audio.sample_rate} Hz | {self.audio.num_channels} channels")
        self.play_pause_button.config(state="normal")

    def save_file(self):
        if not self.audio:
            return

        path = filedialog.asksaveasfilename(defaultextension=".wav")

        if not path:
            return

        save_wav(path, self.audio)
        self.status_var.set(f"Saved: {path}")

    def open_effect_dialog(self, effect_name):
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title(effect_name.capitalize())
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)

        params_frame = tk.Frame(self.dialog)
        params_frame.pack(padx=10, pady=10)

        self.build_params(params_frame, effect_name)

        tk.Button(self.dialog, text="Apply effect", command=lambda: self.apply_effect(effect_name, self.dialog)).pack(pady=10)

    def build_params(self, parent, effect):
        self.param_widgets.clear()
        params = get_effect_params(effect)

        for name, meta in params.items():
            frame = tk.Frame(parent)
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

    def apply_effect(self, effect, dialog):
        if not self.audio:
            messagebox.showerror("Error", "No audio loaded")
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

        self.status_var.set("Processing...")
        self.play_pause_button.configure(state="disabled")

        chain = [(effect, params)]
        #self.audio = apply_chain(self.audio, chain, parallel=True)
        thread = threading.Thread(
            target = self.process_audio,
            args = (self.audio, chain),
            daemon = True
        )
        thread.start()

        self.root.after(100, self.check_queue)

        dialog.destroy()

    def process_audio(self, audio, chain):
        try:
            start = time.perf_counter()
            result = apply_chain(audio, chain, parallel=True)
            end = time.perf_counter()
            duration = end - start
            effect_name = chain[0][0]

            print(f"[EFFECT: {effect_name}] [TIME: {duration:.4f}]")

            self.queue.put(("success", result))
        except Exception as e:
            self.queue.put(("error", str(e)))

    def check_queue(self):
        try:
            status, data = self.queue.get_nowait()

            if status == "success":
                self.audio = data
                self.rebuild_cache()
                self.draw_waveform()
                self.status_var.set("Effect applied successfully")
                self.play_pause_button.configure(state="normal")
            elif status == "error":
                self.status_var.set("Error")
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

    def rebuild_cache(self):
        if not self.audio:
            self.audio_data = None
            return

        arr = np.array(self.audio.samples, dtype=np.float32)

        if self.audio.num_channels > 1:
            arr = arr.reshape(-1, self.audio.num_channels)

        self.audio_data = arr

    def toggle_play_pause(self):
        if not self.audio:
            return

        if self.paused:
            self.resume_audio()
        elif self.playing:
            self.pause_audio()
        else:
            self.play_audio()

    def play_audio(self):
        sd.play(self.audio_data, samplerate=self.audio.sample_rate)

        self.play_start_time = time.time()
        self.playing = True
        self.paused = False
        self.pause_time = 0
        self.play_pause_button.config(text="⏸ Pause")
        self.stop_button.config(state="normal")

        self.update_cursor()

    def stop_audio(self):
        sd.stop()
        self.playing = False
        self.paused = False
        self.play_start_time = 0
        self.pause_time = 0
        self.play_pause_button.config(text="▶ Play")
        self.stop_button.config(state="disabled")
        self.canvas.delete("cursor")

    def pause_audio(self):
        if not self.playing or self.paused:
            return

        latency = sd.query_devices(sd.default.device['output'], 'output')['default_low_output_latency']

        sd.stop()
        self.playing = False
        self.paused = True
        self.pause_time = time.time() + latency
        self.play_pause_button.config(text="▶ Resume")

    def resume_audio(self):
        if not self.paused:
            return

        elapsed = self.pause_time - self.play_start_time

        start_sample = int(elapsed * self.audio.sample_rate)
        sliced = self.audio_data[start_sample:]

        sd.play(sliced, samplerate=self.audio.sample_rate)
        self.play_start_time = time.time() - elapsed
        self.playing = True
        self.paused = False
        self.play_pause_button.config(text="⏸ Pause")

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
            self.paused = False
            self.play_start_time = 0
            self.pause_time = 0

            self.play_pause_button.config(text="▶ Play")
            self.stop_button.config(state="disabled")