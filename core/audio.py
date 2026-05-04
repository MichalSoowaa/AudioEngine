class Audio:
    def __init__(self, samples, sample_rate, num_channels=1, sample_width=2):
        self.samples = samples
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_width = sample_width

    def copy(self):
        return Audio(self.samples.copy(), self.sample_rate, self.num_channels, self.sample_width)

INT16_MIN = -32768
INT16_MAX = 32767

def clamp(value: int) -> int:
    return max(INT16_MIN, min(INT16_MAX, value))

def split_channels(audio: Audio):
    if audio.num_channels == 1:
        return [audio.samples]

    channels = [[] for _ in range(audio.num_channels)]

    for i, sample in enumerate(audio.samples):
        ch = i % audio.num_channels
        channels[ch].append(sample)

    return channels

def merge_channels(channels):
    merged = []

    for frame in zip(*channels):
        merged.extend(frame)

    return merged