"""PLY parser declarations; productions carry heterogeneous semantic values."""

from typing import Any

class YaccProduction:
    def __getitem__(self, n: int) -> Any: ...  # noqa: ANN401 - PLY semantic values vary by production.
    def __setitem__(self, n: int, value: object) -> None: ...

def yacc(*, debug: int = ..., write_tables: int = ...) -> object: ...
def parse(input: str) -> object: ...
