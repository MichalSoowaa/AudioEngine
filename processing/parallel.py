from multiprocessing import Pool, cpu_count
from core.audio import Audio, split_channels, merge_channels
from core.enums import ProcessingMode

def process_full(args):
    chunk, effect_func, effect_context, user_params = args
    return effect_func(chunk, effect_context, **user_params).samples

def process_overlap(args):
    audio, start, end, effect_func, effect_context, user_params = args

    ext_start = max(0, start - effect_context.overlap)
    ext_end = end
    extended_samples = audio.samples[ext_start:ext_end]

    chunk = Audio(extended_samples, audio.sample_rate, audio.num_channels, audio.sample_width)
    processed = effect_func(chunk, effect_context, **user_params).samples

    trim_start = start - ext_start
    trim_end = trim_start + (end - start)

    return processed[trim_start:trim_end]

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

def apply_effect_parallel(audio, effect_data, **user_params):
    channels = split_channels(audio)
    processed_channels = []

    for ch_samples in channels:
        ch_audio = Audio(ch_samples, audio.sample_rate, 1, audio.sample_width)
        processed = apply_effect_parallel(ch_audio, effect_data, **user_params)
        processed_channels.append(processed.samples)

    merged_samples = merge_channels(processed_channels)

    return Audio(merged_samples, audio.sample_rate, audio.num_channels, audio.sample_width)

def apply_effect_on_single_channel(audio, effect_data, **user_params):
    mode = effect_data['mode']
    func = effect_data['func']
    preprocess = effect_data['preprocess']

    effect_context = None

    if preprocess:
        effect_context = preprocess(audio, **user_params)

    if mode == ProcessingMode.NORMAL:
        return func(audio, effect_context, **user_params)

    num_workers = min(cpu_count(), len(audio.samples))

    indices = split_indices(len(audio.samples), num_workers)

    with Pool(num_workers) as pool:
        if mode == ProcessingMode.PARALLEL:
            chunks = [
                Audio(audio.samples[start:end], audio.sample_rate, audio.num_channels, audio.sample_width)
                for start, end in indices
            ]

            args = [
                (chunk, func, effect_context, user_params)
                for chunk in chunks
            ]

            results = pool.map(process_full, args)
        elif mode == ProcessingMode.OVERLAP:

            args = [
                (audio, start, end, func, effect_context, user_params)
                for start, end in indices
            ]

            results = pool.map(process_overlap, args)
        else:
            raise ValueError("Unknown mode")

    merged_samples = merge_chunks(results)

    return Audio(merged_samples, audio.sample_rate, audio.num_channels, audio.sample_width)