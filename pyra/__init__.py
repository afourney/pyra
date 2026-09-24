"""Query indexed text with the GCL region algebra and passage ranking."""

import warnings

from .gcl import GCL as GCL
from .icover import CoverDensityRanking as CoverDensityRanking
from .iindex import INF as INF
from .iindex import InvertedIndex as InvertedIndex

warnings.warn(
    "CAUTION: This module is in its infancy, and has many bugs!", ImportWarning, stacklevel=2
)
