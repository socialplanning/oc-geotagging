import warnings
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.viewlet.viewlet import ViewletBase
from opencore.browser.base import _
from opencore.configuration.utils import get_config
from opencore.geotagging.view import get_geo_writer, get_geo_reader

from urlparse import urlparse

class GeoViewlet(ViewletBase):

    sort_order = 123  # we'll sort this out later. HA HA I FUNNY

    @property
    def geo_info(self):
        """geo information for display in forms;
        takes values from request, falls back to existing project
        if possible."""
        # I suspect these viewlets are going to totally replace the
        # stuff in geotagging/view.py; right now, just trying to get
        # tests passing again.
        geo = get_geo_reader(self.__parent__)
        return geo.geo_info()

    def validate(self):
        view = self.__parent__  # XXX is there another idiom for this?
        geowriter = get_geo_writer(view)
        geo_info, locationchanged = geowriter.get_geo_info_from_form()
        errors = geo_info.get('errors', {})
        return errors
        

    def update(self):
        """Save coordinates and any other geo info, if necessary."""
        view = self.__parent__  # XXX is there another idiom for this?
        geowriter = get_geo_writer(view)
        geo_info, locationchanged = geowriter.get_geo_info_from_form()
        errors = geo_info.get('errors', {})
        if errors:
            view.errors.update(errors)
        elif locationchanged:
            geowriter.save_coords_from_form()
            view.add_status_message(_(u'psm_location_changed'))
        

class ProjectViewlet(GeoViewlet):

    render = ZopeTwoPageTemplateFile('project_viewlet.pt')

    
class MemberProfileViewlet(GeoViewlet):

    render = ZopeTwoPageTemplateFile('profile_viewlet.pt')


class MemberProfileEditViewlet(GeoViewlet):

    render = ZopeTwoPageTemplateFile('profile_edit_viewlet.pt')



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
    
