#!/usr/bin/env python

def make_chamber_pos():
    chamber_pos = []

    for tray in xrange(1,17):
        for t_col in ['A', 'B', 'C', 'D']:
            for t_row in xrange(1, 6):
                chamber_pos.append("%d%s%d" % (tray, t_col, t_row))

    for iii, pos in enumerate(chamber_pos):
        yield "%i\t%s" % (iii + 1, pos)

if __name__ == "__main__":
    for s in make_chamber_pos():
        print s
