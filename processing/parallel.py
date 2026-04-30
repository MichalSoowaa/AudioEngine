from multiprocessing import Pool, cpu_count
from core.audio import Audio

def process_full(args):
    chunk, effect_func, params = args
    return effect_func(chunk, **params).samples

def process_overlap(args):
    audio, start, end, effect_func, overlap, params = args

    ext_start = max(0, start - overlap)
    ext_end = end
    extended_samples = audio.samples[ext_start:ext_end]

    chunk = Audio(extended_samples, audio.sample_rate, audio.num_channels, audio.sample_width)
    processed = effect_func(chunk, **params).samples

    trim_start = start - ext_start
    trim_end = trim_start + (end - start)

    return processed[trim_start:trim_end]

# def split_audio(audio, num_chunks):
#     length = len(audio.samples)
#     chunk_size = length // num_chunks
#     chunks = []
#
#     for i in range(num_chunks):
#         start = i * chunk_size
#         end = length if i == num_chunks - 1 else start + chunk_size
#
#         chunk_samples = audio.samples[start:end]
#         chunk = Audio(chunk_samples, audio.sample_rate, audio.num_channels, audio.sample_width)
#
#         chunks.append(chunk)
#
#     return chunks

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

def apply_effect_parallel(audio, effect_data, **params):
    mode = effect_data['mode']
    func = effect_data['func']
    preprocess = effect_data['preprocess']

    if preprocess:
        extra = preprocess(audio, **params)
        params.update(extra)

    if mode == "none":
        return func(audio, **params)

    num_workers = cpu_count()

    indices = split_indices(len(audio.samples), num_workers)

    with Pool(num_workers) as pool:
        if mode == "parallel":
            chunks = [
                Audio(audio.samples[start:end], audio.sample_rate, audio.num_channels, audio.sample_width)
                for start, end in indices
            ]

            args = [
                (chunk, func, params)
                for chunk in chunks
            ]

            results = pool.map(process_full, args)
        elif mode == "overlap":
            overlap = params.pop('overlap')

            args = [
                (audio, start, end, func, overlap, params)
                for start, end in indices
            ]

            results = pool.map(process_overlap, args)
        else:
            raise ValueError("Unknown mode")

    merged_samples = merge_chunks(results)

    return Audio(merged_samples, audio.sample_rate, audio.num_channels, audio.sample_width)