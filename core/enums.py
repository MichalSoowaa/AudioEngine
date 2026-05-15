from enum import Enum

class ProcessingMode(Enum):
    NORMAL = "normal"
    PARALLEL = "parallel"
    OVERLAP = "overlap"
    FRAMES = "frames"
    BLOCKS = "blocks"