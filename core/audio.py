INT16_MIN = -32768
INT16_MAX = 32767

def clamp(value: int) -> int:
    return max(INT16_MIN, min(INT16_MAX, value))

class Audio:
    def __init__(self, samples, sample_rate, num_channels=1, sample_width=2):
        self.samples = samples
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_width = sample_width

    def copy(self):
        return Audio(self.samples.copy(), self.sample_rate, self.num_channels, self.sample_width)
