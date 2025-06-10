# https://github.com/kala-telo/arrows.py

from enum import IntEnum, auto
import base64

class Direction(IntEnum):
    North = auto(),
    East  = auto(),
    South = auto(),
    West  = auto()

class ArrowType(IntEnum):
    Empty                  = auto(),
    Arrow                  = auto(),
    Source                 = auto(),
    Blocker                = auto(),
    Delay                  = auto(),
    Detector               = auto(),
    SplitterUpDown         = auto(),
    SplitterUpRight        = auto(),
    SplitterUpRightLeft    = auto(),
    Pulse                  = auto(),
    BlueArrow              = auto(),
    Diagonal               = auto(),
    BlueSplitterUpUp       = auto(),
    BlueSplitterRightUp    = auto(),
    BlueSplitterUpDiagonal = auto(),
    Not                    = auto(),
    And                    = auto(),
    Xor                    = auto(),
    Latch                  = auto(),
    Flipflop               = auto(),
    Random                 = auto(),
    Button                 = auto(),
    LevelSource            = auto(),
    LevelTarget            = auto(),
    DirectoinalButton      = auto(),
    Unknown                = auto(),


class Arrow:
    def __init__(self, type: ArrowType = ArrowType.Empty, direction: Direction = Direction.North, flipped = False):
        self.type = type
        self.direction = direction
        self.flipped = flipped

    direction: Direction = Direction.North
    flipped: bool = False
    type: ArrowType = ArrowType.Empty

class Chunk:
    arrows: list[Arrow]
    def __init__(self):
        self.arrows = [Arrow()] * 256

    def get(self, x: int, y: int) -> Arrow:
        return self.arrows[y*16+x]
    def set(self, x: int, y: int, arrow: Arrow):
        self.arrows[y*16+x] = arrow

class Map:
    version: int = 0
    chunks: dict[tuple[int, int], Chunk] = {}

    def __init__(self, string: None|str = None):
        if string is not None:
            self.import_(string)

    def get(self, x: int, y: int) -> Arrow:
        chunk_x = x//16
        chunk_y = y//16
        arrow_x = x % 16
        arrow_y = y % 16
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk()
        return self.chunks[(chunk_x, chunk_y)].get(arrow_x, arrow_y)

    def set(self, x: int, y: int, arrow: Arrow):
        chunk_x = x//16
        chunk_y = y//16
        arrow_x = x % 16
        arrow_y = y % 16
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk()

        self.chunks[(chunk_x, chunk_y)].set(arrow_x, arrow_y, arrow)

    def import_(self, string: str, x_: int = 0, y_: int = 0):
        raw_data = base64.b64decode(string)
        def pop8() -> int:
            nonlocal raw_data
            val = raw_data[:1]
            raw_data = raw_data[1:]
            return int.from_bytes(val, byteorder='little')
        def pop16() -> int:
            nonlocal raw_data
            val = raw_data[:2]
            raw_data = raw_data[2:]
            return int.from_bytes(val, byteorder='little')

        self.version = pop16()
        chunks_count = pop16()
        for _ in range(chunks_count):
            chunk_x = pop16()
            chunk_y = pop16()
            arrow_types = pop8()+1
            for _ in range(arrow_types):
                type = pop8()
                type_count = pop8()+1
                for _ in range(type_count):
                    position = pop8()
                    x = position & 0x0F
                    y = (position & 0xF0) >> 4
                    direction_and_flipped = pop8()
                    direction = direction_and_flipped & 0b011
                    flipped = direction_and_flipped & 0b100 != 0
                    arrow = Arrow()
                    arrow.flipped = flipped
                    arrow.type = ArrowType(type+1)
                    arrow.direction = Direction(direction+1)
                    self.set(chunk_x*16 + x + x_, chunk_y*16 + y + y_, arrow)

    def export(self) -> str:
        raw_data = bytearray([])
        def push8(val: int):
            nonlocal raw_data
            raw_data.extend(val.to_bytes(byteorder='little', length=1))
        def push16(val: int):
            nonlocal raw_data
            raw_data.extend(val.to_bytes(byteorder='little', length=2))


        push16(self.version)
        push16(len(self.chunks))
        for cords, chunk in self.chunks.items():
            types = []
            for arrow in chunk.arrows:
                if arrow.type != ArrowType.Empty and arrow.type not in types:
                    types.append(arrow.type)
            if types == []: continue
            push16(cords[0])
            push16(cords[1])
            push8(len(types)-1)
            for type in types:
                push8(type-1)
                push8(0)
                types_count_index = len(raw_data)-1
                types_count = 0
                for x in range(16):
                    for y in range(16):
                        arrow = chunk.get(x, y)
                        if arrow.type != type: continue
                        position = x | (y<<4)
                        rotation = (arrow.direction-1) | (arrow.flipped << 2)
                        push8(position)
                        push8(rotation)
                        types_count += 1
                raw_data[types_count_index] = types_count-1
        return base64.b64encode(raw_data).decode('utf-8')
