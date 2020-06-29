import sys
import os
import os.path
import subprocess
import re

import util
from filelayout import latex_dir

#
# For some reason the first equation in a preview environment seems to get
# a slightly different alignment than all the others, so we add a dummy equation
# to the front.
#

# \\documentclass[fontsize=12pt, fleqn]{scrartcl}
latex_header = """
\\documentclass[fontsize=12pt, fleqn]{article}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage[active,tightpage]{preview}
\\begin{document}

\\large

\\begin{preview}
\\noindent
$ignore$
\\end{preview}

"""

latex_body = """
\\begin{{preview}}
\\noindent
${}$
\\end{{preview}}
"""

latex_footer = """
\\end{document}
"""

class LatexEquation:
    def __init__(self, latex, inline):
        self.latex = latex
        self.inline = inline
        self.svg_path = None
        self.svg_geometry = None
        self.png_path = None
        self.png_geometry = None

    def alt_text(self):
        if len(self.latex) > 200:
            return self.latex[:197] + '...'
        else:
            return self.latex

    def to_code(self):
        if self.inline:
            return self.latex
        else:
            return '\\displaystyle ' + self.latex

def latex_document(equations):
    assert len(equations) > 0
    body = [latex_body.format(equation.to_code()) for equation in equations]
    return ''.join([latex_header] + body + [latex_footer])

def remove_old_files():
    for filename in os.listdir(latex_dir):
        if filename.endswith('.svg') or filename.endswith('.png'):
            os.remove(os.path.join(latex_dir, filename))

_dvisvgm_re = re.compile('  width=(\\d*\\.\\d+)pt, height=(\\d*\\.\\d+)pt, depth=(\\d*\\.\\d+)pt')
def parse_dvisvgm_stderr(output):
    result = []
    for line in output.splitlines():
        match = _dvisvgm_re.fullmatch(line)
        if match:
            result.append((
                float(match.group(1)),
                float(match.group(2)),
                float(match.group(3))))
    return result

_dvipng_re = re.compile('\\s*depth=(\\d+) height=(\\d+) width=(\\d+)')
def parse_dvipng_stdout(output):
    result = []
    for depth, height, width in _dvipng_re.findall(output):
        result.append((int(width), int(height), int(depth)))
    return result

def makeimages(equations, make_svg = False, make_png = True, png_dpi = 96):
    N = len(equations)
    if N == 0 or not (make_svg or make_png):
        return

    remove_old_files()

    basename = 'equations'
    filename = basename + '.tex'
    fp = os.path.join(latex_dir, filename)
    with open(fp, 'w') as f:
        f.write(latex_document(equations))

    try:
        util.call(['latex', '-halt-on-error', filename], cwd = latex_dir)
    except subprocess.CalledProcessError:
        return

    if make_svg:
        dvisvgm_cmd = ['dvisvgm', '--no-fonts', '--exact-bbox', '--page=-',
                '--bbox=preview', '--output=%f-%4p.svg', basename + '.dvi']
        dvisvgm_result = util.call(dvisvgm_cmd, cwd = latex_dir)
        geometry = parse_dvisvgm_stderr(dvisvgm_result.stderr)
        assert len(geometry) == N + 1

        images = []
        for filename in os.listdir(latex_dir):
            if filename.endswith('.svg'):
                images.append(filename)
        assert len(images) == N + 1
        images.sort()

        for i in range(N):
            equations[i].svg_path = os.path.join(latex_dir, images[i + 1])
            equations[i].svg_geometry = geometry[i + 1] # Tuple of width, height, depth

    if make_png:
        dvipng_cmd = ['dvipng', '--width', '--height', '--depth', '-D', str(png_dpi),
                '-T', 'tight', '-z', '9', '--gamma', '3',
                '-q', '-o', basename + '-%04d.png', basename + '.dvi']
        dvipng_result = util.call(dvipng_cmd, cwd = latex_dir)
        geometry = parse_dvipng_stdout(dvipng_result.stdout)
        assert len(geometry) == N + 1

        images = []
        for filename in os.listdir(latex_dir):
            if filename.endswith('.png'):
                images.append(filename)
        assert len(images) == N + 1
        images.sort()

        for i in range(N):
            equations[i].png_path = os.path.join(latex_dir, images[i + 1])
            equations[i].png_geometry = geometry[i + 1] # Tuple of width, height, depth
