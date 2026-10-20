from typing import TypedDict


class FileAnalysis(TypedDict):
    lines: int
    functions: list[str]
    classes: list[str]
    imports: list[str]