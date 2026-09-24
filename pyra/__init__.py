"""Query indexed text with the GCL region algebra and passage ranking."""

import warnings

from .gcl import GCL as GCL
from .icover import CoverDensityRanking as CoverDensityRanking
from .iindex import INF as INF
from .iindex import InvertedIndex as InvertedIndex
from .text import CheckpointIndex as CheckpointIndex
from .text import FileTextSource as FileTextSource
from .text import PassageReader as PassageReader
from .text import RegexTokenizer as RegexTokenizer
from .text import StringTextSource as StringTextSource
from .text import TextSource as TextSource
from .text import Token as Token
from .text import Tokenizer as Tokenizer

warnings.warn(
    "CAUTION: This module is in its infancy, and has many bugs!", ImportWarning, stacklevel=2
)
