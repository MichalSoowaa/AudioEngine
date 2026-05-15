from os import cpu_count

import numpy as np

from core.audio import Audio
from processing.runner import run_parallel
from processing.strategies.base import ProcessingStrategy


def make_blocks(samples, block_size, hop_size):
    blocks = []

    for start in range(0, len(samples) - block_size, hop_size):
        block = np.array(samples[start:start + block_size], dtype=np.float32)
        blocks.append((start, block))

    return blocks

def overlap_add(blocks, total_length):
    output = np.zeros(total_length)

    for start, block in blocks:
        end = min(start + len(block), total_length)
        output[start:end] += block[:end - start]

    return output

class BlockStrategy(ProcessingStrategy):
    @staticmethod
    def worker(args):
        start, block, effect_func, context, user_params = args
        processed = effect_func(block, context, **user_params)

        return start, processed

    @staticmethod
    def apply(audio, effect_func, context, parallel, user_params):
        blocks = make_blocks(audio.samples, context.block_size, context.hop_size)

        if parallel:
            workers = cpu_count()
            tasks = [(start, block, effect_func, context, user_params) for start, block in blocks]

            results = run_parallel(tasks, BlockStrategy.worker, workers)
        else:
            results = []

            for start, block in blocks:
                processed = effect_func(block, context, **user_params)
                results.append((start, processed))

        output = overlap_add(results, len(audio.samples))
        output = np.clip(output, -1.0, 1.0)

        return Audio(output.tolist(), audio.sample_rate, audio.num_channels, audio.sample_width)