from Globals import DevelopmentMode
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.PleiadesGeocoder.browser.info import GeoInfosetView
from opencore.browser import tal
import cStringIO
import logging
import traceback
import os.path

logger = logging.getLogger('opencore.geotagging.feeds')

_rss_head = '''<?xml version="1.0" encoding="utf-8"?>
<feed
 xmlns="http://www.w3.org/2005/Atom"
 xmlns:georss="http://www.georss.org/georss"
 xmlns:gml="http://www.opengis.net/gml">

<title>%(title)s</title>
<link rel="self" href="%(folder_url)s"/>
<updated/>
<author/>
<id>%(folder_url)s</id>

'''

_rss_point = '''<entry>
<title>%(title)s</title>
<link rel="alternate" href="%(link)s">%(link)s</link>
<id>%(link)s</id>
<updated>%(updated)s</updated>
<summary>%(description)s</summary>
<georss:where><gml:Point>
<gml:pos>%(coords_georss)s</gml:pos>
</gml:Point></georss:where>
</entry>
'''

_rss_linestring = '''<entry>
<title>%(title)s</title>
<link rel="alternate" href="%(link)s">%(link)s</link>
<id>%(link)s</id>
<updated>%(updated)s</updated>
<summary>%(description)s</summary>
<georss:where><gml:LineString>
<gml:posList>%(coords_georss)s</gml:posList>
</gml:LineString></georss:where>
</entry>
'''

_rss_polygon = '''<entry>
<title>%(title)s</title>
<link rel="alternate" href="%(link)s">%(link)s</link>
<id>%(link)s</id>
<updated>%(updated)s</updated>
<summary>%(description)s</summary>
<georss:where>
<gml:Polygon><gml:exterior><gml:LinearRing>
<gml:posList>%(coords_georss)s</gml:posList>
</gml:LinearRing></gml:exterior></gml:Polygon>
</georss:where>
</entry>
'''

_rss_tail = '\n</feed>\n'


class XmlPageTemplateFile(ZopeTwoPageTemplateFile):

    """This class exists because the process whereby PageTemplateFile
    decides whether to use HTML or XML mode for parsing and validation
    is completely stupid.
    """
    
    content_type = 'text/xml'

    def _cook_check(self):
        # In PageTemplateFile, this gets called potentially multiple
        # times (if you're in dev mode), sniffs the file's content,
        # and if it doesn't start with an XML declaration, uses HTML
        # mode.  We don't want that.  So here, we duplicate the same
        # code without the sniffing.
        if self._v_last_read and not DevelopmentMode:
            return
        __traceback_info__ = self.filename
        try:
            mtime = os.path.getmtime(self.filename)
        except OSError:
            mtime = 0
        if self._v_program is not None and mtime == self._v_last_read:
            return
        t = self.content_type  # Take my word for it, dammit!
        f = open(self.filename, "rb")
        if t != "text/xml":
            # For HTML, we really want the file read in text mode:
            f.close()
            f = open(self.filename, 'U')
            text = ''
        text = f.read()
        f.close()
        self.pt_edit(text, t)
        self._cook()
        if self._v_errors:
            logger.error('Error in template: %s' % '\n'.join(self._v_errors))
            return
        self._v_last_read = mtime


class GeoRssView(GeoInfosetView):

    template = ZopeTwoPageTemplateFile('georss_point.zpt')
    
    def georss(self):
        """Stream a GeoRSS xml feed for this container.
        """
        # XXX we should support conditional GET, if we had a way
        # to find out which items have changed coordinates.
        response = self.request.RESPONSE
        maxitems = int(self.request.form.get('maxitems', -1))
        response.setHeader('Content-Type',
                           'application/atom+xml; charset=utf-8')
        headinfo = {'folder_url': self.context.absolute_url(),
                    'title': self.context.title_or_id(),
                    }
        items = self.forRSS(maxitems)
        # Do streaming, old-school zserver & http 1.0 style.
        response._http_connection = 'close'
        response.http_chunk = 0
        response.setStatus(200)
        response.write(_rss_head % headinfo)
        try:
            for item in items:
                properties = item['properties']
                properties['description'] = properties.get('description') or 'None.'
                properties['coords_georss'] = item['coords_georss']
                if item['hasPoint']:
                    macro = self.template.macros['point_macro']
                    macro_context = tal.create_tal_context(self, options=properties)
                    snippet = tal.render(macro, macro_context,
                                         macros=self.template.macros)
                    response.write(snippet.encode('utf8'))
##                    response.write(_rss_point % properties)
                elif item['hasLineString']:
                    response.write(_rss_linestring % properties)
                elif item['hasPolygon']:
                    response.write(_rss_polygon % properties)
                else:
                    continue
        except:
            # Yuck. ZServer can't tolerate exceptions once you've
            # started streaming with response.write().
            # Best we can do now is log the exception.
            f = cStringIO.StringIO()
            traceback.print_exc(file=f)
            logger.error(f.getvalue())
        response.write(_rss_tail)
        response.flush()
