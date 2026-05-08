class Audio:
    def __init__(self, samples, sample_rate, num_channels=1, sample_width=2):
        self.samples = samples
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_width = sample_width

    def copy(self):
        return Audio(self.samples.copy(), self.sample_rate, self.num_channels, self.sample_width)

INT_MIN = -1.0
INT_MAX = 1.0

def clamp(value: int) -> float:
    return max(INT_MIN, min(INT_MAX, value))

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