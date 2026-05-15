from os import cpu_count

import numpy as np

from core.audio import Audio
from processing.runner import run_parallel
from processing.strategies.base import ProcessingStrategy

def make_frames(samples, frame_size, hop_size):
    frames = []

    for start in range(0, len(samples), hop_size):
        frame = samples[start:start + frame_size]

        if(len(frame) < frame_size):
            padded = np.zeros(frame_size, dtype=np.float32)
            padded[:len(frame)] = frame
            frame = padded
        else:
            frame = np.array(frame, dtype=np.float32)

        frames.append((start, frame))

    return frames

class FrameStrategy(ProcessingStrategy):
    @staticmethod
    def worker(args):
        frames, effect_func, context, user_params = args

        return effect_func(frames, context, **user_params)

    @staticmethod
    def apply(audio, effect_func, context, parallel, user_params):
        if parallel:
            return FrameStrategy.apply_parallel(audio=audio, effect_func=effect_func, context=context, user_params=user_params)
        else:
            # print("XDDDDDDDDDD")
            frames = make_frames(audio.samples, context.frame_size, context.hop_size)
            processed_frames = effect_func(frames, context, **user_params)
            output = context.reconstruct(processed_frames)
            output = np.clip(output, -1.0, 1.0)

            return Audio(output.tolist(), audio.sample_rate, audio.num_channels, audio.sample_width)

    @staticmethod
    def apply_parallel(audio, effect_func, context, user_params):
        frames = make_frames(audio.samples, context.frame_size, context.hop_size)
        workers = cpu_count()
        chunk_size = max(1, len(frames) // workers)
        frame_chunks = [frames[i:i + chunk_size] for i in range(0, len(frames), chunk_size)]
        tasks = [(chunk, effect_func, context, user_params) for chunk in frame_chunks]
        results = run_parallel(tasks, FrameStrategy.worker, workers)

        all_frames = [frame for chunk in results
                      for frame in chunk]

        output = context.reconstruct(all_frames)
        output = np.clip(output, -1.0, 1.0)

        return Audio(output.tolist(), audio.sample_rate, audio.num_channels, audio.sample_width)