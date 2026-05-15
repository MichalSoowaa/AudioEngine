from multiprocessing import cpu_count

from core.audio import Audio
from processing.runner import run_parallel
from processing.strategies.base import ProcessingStrategy


def split_indices(length, num_chunks):
    chunk_size = length // num_chunks
    indices = []

    for i in range(num_chunks):
        start = i * chunk_size
        end = length if i == num_chunks - 1 else start + chunk_size
        indices.append((start, end))

    return indices

def merge_chunks(chunks):
    merged = []

    for chunk in chunks:
        merged.extend(chunk)

    return merged

class ParallelStrategy(ProcessingStrategy):
    @staticmethod
    def worker(args):
        chunk, effect_func, context, user_params = args

        return effect_func(chunk, context, **user_params).samples

    @staticmethod
    def apply(audio, effect_func, context, parallel, user_params):
        if parallel:
            return ParallelStrategy.apply_parallel(audio, effect_func, context, user_params)
        else:
            return effect_func(audio, context, **user_params)

    @staticmethod
    def apply_parallel(audio, effect_func, context, user_params):
        num_workers = min(cpu_count(), len(audio.samples))

        indices = split_indices(len(audio.samples), num_workers)
        chunks = [Audio(audio.samples[start:end], audio.sample_rate, audio.num_channels, audio.sample_width)
                  for start, end in indices]

        num_workers = min(cpu_count(), len(chunks))

        tasks = [(chunk, effect_func, context, user_params) for chunk in chunks]
        results = run_parallel(tasks, ParallelStrategy.worker, num_workers)
        merged = merge_chunks(results)

        return Audio(merged, audio.sample_rate, audio.num_channels, audio.sample_width)
