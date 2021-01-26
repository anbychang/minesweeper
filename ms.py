#!/usr/bin/env python3

from io import BytesIO

import cairo
from IPython.display import SVG, display


class Board():

    BUMP_CELL = 'x'
    NEARBY = [[-1, -1], [0, -1], [1, -1],
              [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]]
    NON_BUMP_CELL = '.'
    SIGNATURE_CELL = 's'
    UNKNOWN_CELL = '?'

    def __init__(self, template: str) -> None:
        self.template = [list(v) for v in template.strip().splitlines()]
        self.height = len(self.template)
        self.width = len(self.template[0])
        self.bumps = [[Board.NON_BUMP_CELL] *
                      self.width for y in range(self.height)]
        self.signatures = {}

    def common_chars(lines: list) -> str:
        common = ''
        n = len(lines)
        for v in zip(*lines):
            common += v[0] if v.count(v[0]) == n else Board.UNKNOWN_CELL
        return common

    def compute_signature(self) -> None:
        board = ''
        key = ''
        for y in range(self.height):
            for x in range(self.width):
                if self.template[y][x] == Board.UNKNOWN_CELL:
                    board += self.bumps[y][x]
                    continue
                elif self.template[y][x] != Board.SIGNATURE_CELL:
                    board += self.template[y][x]
                    continue
                count = 0
                for x2, y2 in [(x+i, y+j) for i, j in Board.NEARBY]:
                    if 0 <= x2 < self.width and 0 <= y2 < self.height and self.bumps[y2][x2] == Board.BUMP_CELL:
                        count += 1
                if count == 0:
                    return
                board += str(count)
                key += str(count)
            board += '\n'

        board = board.strip()
        if key in self.signatures:
            self.signatures[key].append(board)
        else:
            self.signatures[key] = [board]

    def draw_cell(context: object, x: int, y: int, cell_size: int, text: str, background_color: tuple, frame_color: tuple, text_color: tuple) -> None:
        if background_color:
            context.rectangle(x, y, cell_size, cell_size)
            context.set_source_rgb(*background_color)
            context.fill()

        if frame_color:
            context.rectangle(x, y, cell_size, cell_size)
            context.set_source_rgb(*frame_color)
            context.stroke()

        if text_color:
            _, _, w, h, _, _ = context.text_extents(text)
            context.move_to(x + cell_size/2 - w/2, y + cell_size/2 + h/2)
            context.set_source_rgb(*text_color)
            context.show_text(text)

    def draw_string(s: str, cell_size: int = 20, font_family: str = 'Consolas', font_size: int = 12) -> None:
        s = [list(v) for v in s.strip().splitlines()]

        height = len(s)
        width = len(s[0])

        svgio = BytesIO()
        with cairo.SVGSurface(svgio, width*cell_size, height*cell_size) as surface:
            context = cairo.Context(surface)
            context.select_font_face(font_family)
            context.set_font_size(font_size)
            context.set_line_width(1)

            for y in range(height):
                for x in range(width):
                    if s[y][x] == ' ':
                        continue
                    if s[y][x] == '?':
                        kwargs = {  # {{{
                            'background_color': (1, .5, 0),
                            'frame_color': (0, 0, 0),
                            'text_color': (1, 1, 1)
                        }  # }}}
                    elif s[y][x] == '|':
                        kwargs = {  # {{{
                            'background_color': (0, 0, 0),
                            'frame_color': None,
                            'text_color': None
                        }  # }}}
                    elif s[y][x] == Board.BUMP_CELL:
                        kwargs = {  # {{{
                            'background_color': (1, .2, .2),
                            'frame_color': (0, 0, 0),
                            'text_color': (1, 1, 1)
                        }  # }}}
                    elif s[y][x] == Board.NON_BUMP_CELL:
                        kwargs = {  # {{{
                            'background_color': (0, .8, 0),
                            'frame_color': (0, 0, 0),
                            'text_color': (1, 1, 1)
                        }  # }}}
                    else:
                        kwargs = {  # {{{
                            'background_color': None,
                            'frame_color': (0, 0, 0),
                            'text_color': (0, 0, 0)
                        }  # }}}
                    Board.draw_cell(
                        context, x*cell_size, y*cell_size, cell_size, s[y][x], **kwargs)
        display(SVG(data=svgio.getvalue()))

    def show_signature(self, string: bool = True, figure: bool = False, **kwargs) -> None:
        for signature, boards in self.signatures.items():
            print(signature, len(boards))
            s = ''
            lines = [v.splitlines() for v in boards]
            for line in zip(*lines):
                common = Board.common_chars(line)
                s += common + '  ' + ' '.join(line) + '\n'
            if string:
                print(s)
            if figure:
                Board.draw_string(s, **kwargs)

    def solve(self, x: int = 0, y: int = 0) -> None:
        if x == self.width:
            x = 0
            y += 1
        if y == self.height:
            self.compute_signature()
            return
        if self.template[y][x] == Board.UNKNOWN_CELL:
            # assume that (x, y) has a bump
            self.bumps[y][x] = Board.BUMP_CELL
            if self.validate(x, y):
                self.solve(x+1, y)
            self.bumps[y][x] = Board.NON_BUMP_CELL  # restore
        self.solve(x+1, y)

    def validate(self, x: int, y: int) -> bool:
        return True
        for x2, y2 in [(x+i, y+j) for i, j in Board.NEARBY]:
            if 0 <= x2 < self.width and 0 <= y2 < self.height and self.template[y2][x2] == '0':
                return False
        return True


if __name__ == '__main__':
    # template code
    #   ?: unknown cell, need to determine whether this position is a bump
    #   .: non-bump cell: {0-9, wall}
    #   s: signature cell: {1-9}, used to group boards
    #
    #   ?????
    #   .sss.
    #   .....
    board = Board('''
?????
.sss.
.....
''')
    board.solve()
    board.show_signature(figure=True)
