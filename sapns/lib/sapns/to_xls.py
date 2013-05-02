# -*- coding: utf-8 -*-

import xlwt
import logging
import tg

def to_xls(ds, visible_columns, group_by, totals, title, fn):

    logger = logging.getLogger('to_xls')
    
    wb = xlwt.Workbook()
    ws = wb.add_sheet(title, True)

    MAX_ROW = 65500
    sheet_n = 1

    pos = {}
    widths = {}

    group_by_ = {}
    for g in group_by:
        group_by_[str(g)] = None

    totals_ = { '_': {} }
    for g in group_by + ['_']:
        totals_[str(g)] = {}
        for t in totals:
            totals_[str(g)][t] = None

    row = 0
    for col, lbl in enumerate(ds.labels):
        if ds.cols[col] in visible_columns:
            i = visible_columns.index(ds.cols[col])
            ws.write(row, i, lbl)

            pos[ds.cols[col]] = (i, col,)
            widths[i] = 0

    row += 1

    xfs_general = xlwt.XFStyle()
    xfs_general.num_format_str = 'General'

    xfs_date = xlwt.XFStyle()
    xfs_date.num_format_str = tg.config.get('formats.date.xls', 'dd/mm/yyyy')

    xfs_time = xlwt.XFStyle()
    xfs_time.num_format_str = tg.config.get('formats.time.xls', 'hh:mm')

    format_float_xls = tg.config.get('formats.float.xls', '0.00')

    xfs_float = xlwt.XFStyle()
    xfs_float.num_format_str = format_float_xls

    xfs_total = xlwt.easyxf('font: bold on;')
    xfs_total.num_format_str = format_float_xls

    def end_sheet(ws, row, sheet_n, reset=True):
        # total
        if len(totals) > 0:
            for g in reversed(['_'] + group_by):
                for t in totals:
                    total = totals_[g][t]
                    if total is not None:
                        ws.write(row, pos[t][0], total, xfs_total)
                        
                        width_ = len(unicode(total))
                        if width_ > widths[pos[t][0]]:
                            widths[pos[t][0]] = width_

                        row += 1

        # column width
        for col, col_w in widths.iteritems():
            if col_w < 10:
                col_w += 2

            ws.col(col).width = col_w*256

        if reset:
            sheet_n += 1
            logger.debug('New sheet (%d)' % sheet_n)
            title_ = '%s-%d' % (title[:28], sheet_n)
            ws = wb.add_sheet(title_, True)

            # write "titles row" and reset widths
            row = 0
            for col, lbl in enumerate(ds.labels):
                if ds.cols[col] in visible_columns:
                    i = visible_columns.index(ds.cols[col])
                    ws.write(row, i, lbl)

                    pos[ds.cols[col]] = (i, col,)
                    widths[i] = 0

            row += 1

            return ws, row, sheet_n

    # content
    for data in ds:
        for col in visible_columns:
            if pos.has_key(col):
                break_ = True
                if group_by_.has_key(col):
                    break_ = group_by_[col] != data[col]
                    group_by_[col] = data[col]
                    i = group_by.index(col)

                    if break_:
                        # show totals
                        for j in xrange(len(group_by)-1, i-1, -1):
                            if len(totals) > 0:
                                for t in totals:
                                    if totals_[group_by[j]][t] is not None:
                                        ws.write(row, pos[t][0], totals_[group_by[j]][t], xfs_total)
                                        if row >= MAX_ROW:
                                            ws, row, sheet_n = end_sheet(ws, row, sheet_n)
                                            
                                row += 1

                        # reset totals
                        for j in xrange(i, len(group_by)):
                            for t in totals:
                                totals_[group_by[j]][t] = None

                # sumatorios
                if col in totals:
                    for g in group_by + ['_']:
                        if totals_[g][col] is None:
                            totals_[g][col] = 0

                        totals_[g][col] += data[col] or 0

                if break_:
                    type_ = ds.types[pos[col][1]]

                    p = pos[col][0]

                    width_ = len(unicode(data[col]))
                    if width_ > widths[p]:
                        widths[p] = width_

                    style = xfs_general
                    if type_ == 'date':
                        style = xfs_date

                    elif type_ == 'time':
                        style = xfs_time
                    
                    elif type_ == 'float':
                        style = xfs_float

                    ws.write(row, p, data[col], style)

        row += 1
        if row >= MAX_ROW:
            ws, row, sheet_n = end_sheet(ws, row, sheet_n)

    end_sheet(ws, row, sheet_n, reset=False)

    wb.save(fn)
