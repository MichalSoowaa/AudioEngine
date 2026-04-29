from multiprocessing import Pool, cpu_count
from core.audio import Audio
from effects.registry import get_effect

def process_chunk(args):
    chunk, effect, params, meta = args

    effect = get_effect(effect)
    processed = effect(chunk, **params)

    return processed.samples

def split_audio(audio, num_chunks):
    length = len(audio.samples)
    chunk_size = length // num_chunks
    chunks = []

    for i in range(num_chunks):
        start = i * chunk_size
        end = length if i == num_chunks - 1 else start + chunk_size

        chunk_samples = audio.samples[start:end]
        chunk = Audio(chunk_samples, audio.sample_rate, audio.num_channels, audio.sample_width)

        chunks.append(chunk)

    return chunks

def merge_chunks(chunks):
    merged = []

    for chunk in chunks:
        merged.extend(chunk)

    return merged

def apply_effect_parallel(audio, effect, **params):
    num_workers = cpu_count()
    chunks = split_audio(audio, num_workers)

    args = [
        (chunk, effect, params, None)
        for chunk in chunks
    ]

    with Pool(num_workers) as pool:
        results = pool.map(process_chunk, args)

    merged_samples = merge_chunks(results)

    return Audio(merged_samples, audio.sample_rate, audio.num_channels, audio.sample_width)