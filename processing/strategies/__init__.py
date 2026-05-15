from core.enums import ProcessingMode

from processing.strategies.normal_strategy import NormalStrategy
from processing.strategies.frame_strategy import FrameStrategy
from processing.strategies.parallel_strategy import ParallelStrategy
from processing.strategies.block_strategy import BlockStrategy

PROCESSING_STRATEGIES = {
    ProcessingMode.NORMAL: NormalStrategy,
    ProcessingMode.PARALLEL: ParallelStrategy,
    ProcessingMode.FRAMES: FrameStrategy,
    ProcessingMode.BLOCKS: BlockStrategy
}