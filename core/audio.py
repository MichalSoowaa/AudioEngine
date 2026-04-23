class Audio:
    def __init__(self, samples, sample_rate, num_channels=1, sample_width=2):
        self.samples = samples
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.sample_width = sample_width

    def copy(self):
        return Audio(self.samples.copy(), self.sample_rate, self.num_channels, self.sample_width)