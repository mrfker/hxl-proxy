"""
Controllers for the HXL Proxy
David Megginson
January 2015

License: Public Domain
Documentation: http://hxlstandard.org
"""

from urllib2 import urlopen
import sys

from flask import Response, request, render_template, url_for, stream_with_context

from hxl_proxy import app

from hxl.parser import HXLReader, genHXL, genJSON, genHTML
from hxl.filters import parse_tags, fix_tag
from hxl.filters.count import HXLCountFilter
from hxl.filters.norm import HXLNormFilter
from hxl.filters.sort import HXLSortFilter
from hxl.filters.cut import HXLCutFilter
from hxl.filters.select import HXLSelectFilter, parse_query

@app.route("/")
def home():
    url = request.args.get('url', None)
    return render_template('home.html', url=url)

@app.route("/filter")
def filter():
    name = request.args.get('name', 'Filtered HXL dataset')
    url = request.args['url']
    format = request.args.get('format', 'csv')
    input = urlopen(url)
    source = HXLReader(input)
    filter_count = int(request.args.get('filter_count', 5))
    for n in range(1,filter_count+1):
        filter = request.args.get('filter%02d' % n)
        if filter == 'count':
            tags = parse_tags(request.args.get('tags%02d' % n, ''))
            aggregate_tag = request.args.get('aggregate_tag%02d' % n)
            if aggregate_tag:
                aggregate_tag = fix_tag(aggregate_tag)
            else:
                aggregate_tag = None
            source = HXLCountFilter(source, tags=tags, aggregate_tag=aggregate_tag)
        elif filter == 'sort':
            tags = parse_tags(request.args.get('tags%02d' % n, ''))
            reverse = (request.args.get('reverse%02d' % n) == 'on')
            source = HXLSortFilter(source, tags=tags, reverse=reverse)
        elif filter == 'norm':
            upper_tags = parse_tags(request.args.get('upper_tags%02d' % n, ''))
            lower_tags = parse_tags(request.args.get('lower_tags%02d' % n, ''))
            date_tags = parse_tags(request.args.get('date_tags%02d' % n, ''))
            number_tags = parse_tags(request.args.get('number_tags%02d' % n, ''))
            source = HXLNormFilter(source, upper=upper_tags, lower=lower_tags, date=date_tags, number=number_tags)
        elif filter == 'cut':
            include_tags = parse_tags(request.args.get('include_tags%02d' % n, ''))
            exclude_tags = parse_tags(request.args.get('exclude_tags%02d' % n, ''))
            source = HXLCutFilter(source, include_tags=include_tags, exclude_tags=exclude_tags)
        elif filter == 'select':
            query = parse_query(request.args['query%02d' % n])
            reverse = (request.args.get('reverse%02d' % n) == 'on')
            source = HXLSelectFilter(source, queries=[query], reverse=reverse)

    if format == 'json':
        return Response(genJSON(source), mimetype='application/json')
    elif format == 'html':
        return Response(stream_with_context(stream_template('filter.html', title=name, source=source)))
    else:
        return Response(genHXL(source), mimetype='text/csv')

app.jinja_env.globals['static'] = (
    lambda filename: url_for('static', filename=filename)
)

def decode(s):
    try:
        return unicode(s, 'utf-8')
    except:
        return s

app.jinja_env.globals['unicode'] = (
    decode
)

def stream_template(template_name, **context):
    """From the flask docs - stream a long template result."""
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv