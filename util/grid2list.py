import csv
from docopt import docopt


CLI_OPTS = """
USAGE:
grid2list.py -i <96wellPlate> [-o <table> -s <sep>]

OPTIONS:
    -i <96wellPlate>    A CSV containing a 96 well plate layout
    -o <table>          Output filename[Default: stdout]
    -s <sep>            Output seperator [Default: ,]

grid2list creates a "melted" 96 well plate with columns:
num, cell, value

Hint, to make it tab seperated, the following key strokes should
work: "-s 'ctrl-v then tab'". This will insert a tab character between the
single quotes, which will make it to python as a tab character. Don't use \t
"""

BadCsvError = ValueError("Poorly formatted 96-well plate")
rows = "ABCDEFGH"
cols = ["{:d}".format(iii) for iii in range(1,13)]
cell_names = ["{}{:d}".format(r,c) for r in rows for c in range(1,13)]
def parse_grid(filename):
    cells = {}
    lineno = 0
    with open(filename) as fh:
        rdr = csv.reader(fh)
        for line in rdr:
            if len(line) != 13:
                raise BadCsvError
            if lineno == 0:
                for ccc, col in enumerate(line):
                    if lineno != 0:
                        if str(ccc) != col:
                            raise BadCsvError
            else:
                for ccc, cell in enumerate(line):
                    if ccc == 0:
                        if not cell in {c for c in rows}:
                            return cells
                    else:
                        cell_idx = rows[lineno - 1] + cols [ccc - 1]
                        cells[cell_idx] = cell
            lineno += 1
    return cells


def print_list(cells, outfn, sep):
    lines = []
    lines.append(sep.join(["Index","Cell", "Value"])) # add header
    for iii, cell in enumerate(cell_names):
        lines.append(sep.join((str(iii+1), cell, cells[cell])))
    if outfn != "stdout":
        with open(outfn, "w") as ofh:
            ofh.write("\n".join(lines))
            ofh.write('\n') # final \n
    else:
        for line in lines:
            print line


if __name__ == "__main__":
    opts = docopt(CLI_OPTS)
    grid = parse_grid(opts['-i'])
    print_list(grid, opts['-o'], opts['-s'])
