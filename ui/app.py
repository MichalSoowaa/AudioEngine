import tkinter as tk
from tkinter import filedialog, messagebox

from core.wav import load_wav, save_wav
from processing.pipeline import apply_chain
from effects.registry import list_effects, get_effect_params


class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Editor")
        self.audio = None
        self.selected_effect = None
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

        tk.Button(self.root, text="Apply effect", command=self.apply_effect).pack()

        self.status = tk.Label(self.root, text="Ready")
        self.status.pack()

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])

        if not path:
            return

        self.audio = load_wav(path)
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

        self.params_entries.clear()

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
        self.audio = apply_chain(self.audio, chain, parallel=True)

        self.status.config(text="Done")