#!/usr/bin/env python3

from io import BytesIO

import cairo
from IPython.display import SVG, display


class Minesweeper():

    NEARBY = [[-1, -1], [0, -1], [1, -1],
              [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]]

    SOLVED_BUMP = 'X'
    SOLVED_BUMPER = '/'
    SOLVED_SAFE = 'O'
    SOLVED_SAFER = '/'
    SOLVED_UNKNOWN = '/'

    TEMPLATE_BUMP = 'X'
    TEMPLATE_NUMBER = '012345678'
    TEMPLATE_SAFE = '.'
    TEMPLATE_SIGNATURE = '#'
    TEMPLATE_UNKNOWN = '?'

    COLORS = {
        'default': [None, (0, 0, 0), (0, 0, 0)],
        'template_number': [(.6, .8, 1), (0, 0, 0), (1, 1, 1)],
        '#': [(.2, .6, 1), (0, 0, 0), (1, 1, 1)],
        ' ': [None, None, None],
        '|': [(0, 0, 0), None, None],
        SOLVED_BUMP: [(1, .2, .2), (0, 0, 0), (1, 1, 1)],
        SOLVED_BUMPER: [(1, .4, .4), (0, 0, 0), (1, 1, 1)],
        SOLVED_SAFE: [(0, .8, 0), (0, 0, 0), (1, 1, 1)],
        SOLVED_SAFER: [(0, .6, 0), (0, 0, 0), (1, 1, 1)],
        SOLVED_UNKNOWN: [(1, .5, 0), (0, 0, 0), (1, 1, 1)],
    }

    def __init__(self, template: str) -> None:
        self.template = [list(v) for v in template.strip().splitlines()]
        self.height = len(self.template)
        self.width = len(self.template[0])
        self.bumps = []
        for y in range(self.height):
            self.bumps.append([])
            for x in range(self.width):
                self.bumps[y].append(Minesweeper.SOLVED_BUMP if self.template[y][x] == Minesweeper.TEMPLATE_BUMP else Minesweeper.SOLVED_SAFE)
        self.commons = {}
        self.signatures = {}

    def close_output(self):
        if self.text is not None:
            print(self.text)
            self.text = None
        if self.surface is not None:
            self.surface.finish()
            display(SVG(data=self.svgio.getvalue()))
            self.surface = None

    def compute_common(self, signature: str, boards: list) -> list:
        common = []
        unknown_common = ''

        n = len(boards)
        for y in range(self.height):
            common.append([])
            for x in range(self.width):
                n_bump = sum([1 for board in boards if board[y][x] == Minesweeper.SOLVED_BUMP])
                n_safe = sum([1 for board in boards if board[y][x] == Minesweeper.SOLVED_SAFE])
                if self.template[y][x] == Minesweeper.TEMPLATE_UNKNOWN:
                    if n_bump == n:
                        code = Minesweeper.SOLVED_BUMP
                    elif n_safe == n:
                        code = Minesweeper.SOLVED_SAFE
                    elif n_bump > n_safe:
                        code = Minesweeper.SOLVED_BUMPER
                    elif n_bump < n_safe:
                        code = Minesweeper.SOLVED_SAFER
                    else:
                        code = Minesweeper.SOLVED_UNKNOWN
                    common[y].append(code)
                    unknown_common += code
                else:
                    common[y].append(boards[0][y][x])

        n = len(unknown_common)
        for i, v in enumerate(unknown_common):
            if i * 2 + 1 != n:
                continue
            k = ['-'] * n
            k[i] = v
            k = ''.join(k)
            if k in self.commons:
                self.commons[k].append(signature)
            else:
                self.commons[k] = [signature]

        return common

    def compute_bumps(self, x: int, y: int) -> int:
        n_bumps = 0
        for x2, y2 in [(x+i, y+j) for i, j in Minesweeper.NEARBY]:
            if 0 <= x2 < self.width and 0 <= y2 < self.height and self.bumps[y2][x2] == Minesweeper.SOLVED_BUMP:
                n_bumps += 1
        return n_bumps

    def compute_signature(self) -> None:
        board = []
        signature = ''
        for y in range(self.height):
            board.append([])
            for x in range(self.width):
                if self.template[y][x] == Minesweeper.TEMPLATE_UNKNOWN:
                    board[y].append(self.bumps[y][x])
                elif self.template[y][x] == Minesweeper.TEMPLATE_SIGNATURE:
                    n_bumps = str(self.compute_bumps(x, y))
                    if n_bumps == '0':
                        return
                    board[y].append(n_bumps)
                    signature += n_bumps
                elif self.template[y][x] in Minesweeper.TEMPLATE_NUMBER:
                    if str(self.compute_bumps(x, y)) != self.template[y][x]:
                        return
                    board[y].append(self.template[y][x])
                else:
                    board[y].append(self.template[y][x])

        if signature in self.signatures:
            self.signatures[signature].append(board)
        else:
            self.signatures[signature] = [board]

    def help() -> None:
        print('''
Template Syntax:
  - x: bump
  - 0-8: number
  - .: safe, number is unknown/not a matter
  - #: signature, solve() determines its number, 0 is not allowed
  - ?: unknown, solve() determines whether this cell is a bump

Template Sample:
  .....
  .##1.
  ?????
''')

    def open_output(self, n_boards: int, cell_size: int = 20, figure: bool = False, text: bool = True,
                    font_family: str = 'Consolas', font_size: int = 12, line_width: int = 1) -> None:
        if figure:
            self.cell_size = cell_size
            self.x, self.y = 0, 0
            self.svgio = BytesIO()
            self.surface = cairo.SVGSurface(
                self.svgio, ((n_boards+1)*(self.width+1)-1)*cell_size, self.height*cell_size)
            ctx = cairo.Context(self.surface)
            ctx.select_font_face(font_family)
            ctx.set_font_size(font_size)
            ctx.set_line_width(line_width)
            self.context = ctx  # save context to speed up
        else:
            self.surface = None
        self.text = '' if text else None

    def output_cell(self, text: str, template_cell: str = None) -> None:
        if template_cell and template_cell in Minesweeper.TEMPLATE_NUMBER:
            background_color, frame_color, text_color = Minesweeper.COLORS['template_number']
        elif template_cell in Minesweeper.COLORS:
            background_color, frame_color, text_color = Minesweeper.COLORS[template_cell]
        elif text in Minesweeper.COLORS:
            background_color, frame_color, text_color = Minesweeper.COLORS[text]
        else:
            background_color, frame_color, text_color = Minesweeper.COLORS['default']
        if self.surface is not None:
            ctx, size, x, y = self.context, self.cell_size, self.x, self.y  # abbreviation
            if background_color:
                ctx.rectangle(x, y, size, size)
                ctx.set_source_rgb(*background_color)
                ctx.fill()
            if frame_color:
                ctx.rectangle(x, y, size, size)
                ctx.set_source_rgb(*frame_color)
                ctx.stroke()
            if text_color:
                _, _, w, h, _, _ = ctx.text_extents(text)
                ctx.move_to(x + size/2 - w/2, y + size/2 + h/2)
                ctx.set_source_rgb(*text_color)
                ctx.show_text(text)
            self.x += size
        if self.text is not None:
            self.text += text

    def output_newline(self) -> None:
        if self.surface is not None:
            self.x, self.y = 0, self.y + self.cell_size
        if self.text is not None:
            self.text += '\n'

    def output_signature(self, **kwargs) -> None:
        for signature, boards in [(k, self.signatures[k]) for k in sorted(self.signatures.keys())]:
            if kwargs['figure'] or kwargs['text']:
                print(signature, len(boards))
            common = self.compute_common(signature, boards)
            self.open_output(len(boards), **kwargs)
            for y in range(self.height):
                # common
                for x in range(self.width):
                    self.output_cell(common[y][x], self.template[y][x])
                self.output_cell(' ')

                # per board
                for i, board in enumerate(boards):
                    for x in range(self.width):
                        self.output_cell(board[y][x], self.template[y][x])
                    if i < len(boards) - 1:
                        self.output_cell('|')
                self.output_newline()
            self.close_output()

    def solve(self, x: int = 0, y: int = 0) -> None:
        if x == self.width:
            x, y = 0, y+1
        if y == self.height:
            self.compute_signature()
            return
        if self.template[y][x] == Minesweeper.TEMPLATE_UNKNOWN:
            # assume that (x, y) has a bump
            self.bumps[y][x] = Minesweeper.SOLVED_BUMP
            if self.validate(x, y):
                self.solve(x+1, y)
            self.bumps[y][x] = Minesweeper.SOLVED_SAFE  # restore
        self.solve(x+1, y)

    def validate(self, x: int, y: int) -> bool:
        return True
        for x2, y2 in [(x+i, y+j) for i, j in Minesweeper.NEARBY]:
            if 0 <= x2 < self.width and 0 <= y2 < self.height and self.template[y2][x2] == '0':
                return False
        return True


if __name__ == '__main__':
    Minesweeper.help()
    ms = Minesweeper(template='''
.....
.##1.
?????
''')
    ms.solve()
    ms.output_signature(figure=False, text=True)
