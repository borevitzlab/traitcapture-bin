#!/usr/bin/env python

chamber_pos = []

for tray in xrange(1,17):
    for t_col in ['A', 'B', 'C', 'D']:
        for t_row in xrange(1, 6):
            chamber_pos.append("%d%s%d" % (tray, t_col, t_row))

for iii, pos in enumerate(chamber_pos):
    print "%i\t%s" % (iii + 1, pos)
