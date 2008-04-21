import warnings
from opencore.configuration.utils import get_config
from urlparse import urlparse

class ProjectViewlet:

    sort_order = 123  # we'll sort this out later. HA HA I FUNNY

    def geo_info(self):
        XXX

    def errors(self):
        XXX

    

    
class GeoJSViewlet:

    """provides a <script> tag for pages that need geo-related js
    """

    sort_order = 100
    
    def render(self):
        url = self.request['ACTUAL_URL']
        # In python 2.5, this could be written as urlparse(url).hostname
        hostname = urlparse(url)[1].split(':')[0]
        # We have a map key for each possible hostname in build.ini.
        key = get_config('google_maps_keys', hostname)
        if not key:
            warnings.warn("need a google maps key for %r" % hostname)
            return ''
        url = "http://maps.google.com/maps?file=api&v=2&key=%s" % key
        return '<script src="%s" type="text/javascript"></script>' % url
    
