from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.PleiadesGeocoder.geo import ANNO_KEY
from Products.PleiadesGeocoder.interfaces.simple import IGeoItemSimple
from opencore.browser.base import _
from opencore.browser.octopus import Action
from opencore.geotagging import interfaces
from opencore.geotagging import utils
from opencore.interfaces import IProject
from opencore.utility.interfaces import IProvideSiteConfig
from urlparse import urlparse
from zope.app.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.interface import implements
import warnings

class ReadGeoViewletBase(object):

    """This can be added to a page to show geo info about the context.
    """

    sort_order = 123  # we'll sort this out later. HA HA I FUNNY

    implements(interfaces.IReadGeo)

    def is_geocoded(self):
        """See IReadGeo."""
        coords = self._get_geo_item().coords
        return bool(coords and not None in coords)

    @property
    def geo_info(self):
        """See IReadGeo"""
        info = {'static_img_url': self.location_img_url(),
                'is_geocoded': self.is_geocoded(),
                }
        content = self._get_viewedcontent()
        info['location'] = ''
        coords = self.get_geolocation()
        try:
            lon, lat = coords[:2]
        except (ValueError, TypeError):
            lon, lat = '', ''
        info['position-latitude'] = lat
        info['position-longitude'] = lon
        return info

    def get_geolocation(self):
        """See IReadGeo. Note the output is ordered as (lon, lat, z)."""
        return self._get_geo_item().coords

    def location_img_url(self, width=500, height=300):
        """See IReadGeo."""
        coords = self._get_geo_item().coords
        if not coords:
            return ''
        lon, lat = coords[:2]
        return utils.location_img_url(lat, lon, width, height)


    def _get_geo_item(self):
        return IGeoItemSimple(self._get_viewedcontent())

    def _get_viewedcontent(self):
        # Subclasses should provide this, to find a potentially more
        # relevant context than self.context - namely, the thing we
        # actually want to set/get coordinates on.
        raise NotImplementedError


class WriteGeoViewletBase(ReadGeoViewletBase):

    """This can be added to a form to add a widget for setting the context's location.
    """
    implements(interfaces.IReadWriteGeo)

    new_info = None

    @property
    def errors(self):
        return getattr(self.__parent__, 'errors', {})

    def save(self):
        """Save form data, if changed."""

        view = self.__parent__
        # XXX we've already geocoded in validate(), don't hit google twice!
        geo_info, changes = self.get_geo_info_from_form()
        errors = geo_info.get('errors', {})
        if errors:
            # This shouldn't happen, we should already have called validate()
            view.errors.update(errors)
        elif changes:
            # XXX and yet another google hit...
            self.save_coords_from_form()
            view.add_status_message(_(u'psm_location_changed'))
            
        # Clean up a bit to avoid archetypes trying to handle our form
        # info.
        form = self.request.form
        for key in ('position-latitude', 'position-longitude'):
            if form.has_key(key):
                del form[key]
        
    def validate(self):
        """We're inventing a convention that viewlets used in forms
        can optionally provide a validate() method that returns a dict
        of error messages; the parent view can do what it likes with these.

        This is kind of gunky, but was the most expedient way to
        integrate with our existing forms.
        """

        view = self.__parent__
        geo_info, changed = self.get_geo_info_from_form()
        errors = geo_info.get('errors', {})
        self.new_info = geo_info
        return errors

    def set_geolocation(self, coords):
        """See IWriteGeo."""
        if coords and not None in coords:
            geo = self._get_geo_item()
            # XXX need to handle things other than a point!
            if len(coords) == 2:
                coords = coords + (0.0,)
            if coords != geo.coords:
                geo.setGeoInterface('Point', coords)
                return True
        return False

    def get_geo_info_from_form(self, form=None, old_info=None):
        """See IWriteGeo.
        """
        if form is None:
            form = dict(self.request.form)
            form['location'] = form.get('geolocation')
        if old_info is None:
            old_info = self.geo_info
        new_info, changed = utils.update_info_from_form(
            self.geo_info, form, getToolByName(self.context, 'portal_geocoder'))
        view = self.__parent__
        view.errors.update(new_info.get('errors', {}))
        return new_info, changed

    def save_coords_from_form(self, form=None):
        """See IWriteGeo."""
        new_info, changed = self.get_geo_info_from_form(form)
        lat = new_info.get('position-latitude')
        lon = new_info.get('position-longitude')
        if lat == '': lat = None
        if lon == '': lon = None
        self.set_geolocation((lon, lat))
        return new_info, changed




class ProjectViewlet(ReadGeoViewletBase):

    @property
    def geo_info(self):
        info = super(ProjectViewlet, self).geo_info
        # Override the static map image size. Ugh, sucks to have this in code.
        info['static_img_url'] = self.location_img_url(width=285, height=285)
        return info

    def _get_viewedcontent(self):
        # Find the project in the acquisition context.
        # I tried to call self.view.piv.project and .inproject, et al. but
        # for some reason those return None and False on a closed project.
        # Instead, we walk the acquisition chain by hand.
        for item in self.context.aq_inner.aq_chain:
            if IProject.providedBy(item):
                return item
        # If we get here, it typically means we're in eg. the projects
        # folder because our view is an add view and the project doesn't
        # exist yet. That's OK, we just won't have as much information.
        return None

class ProjectEditViewlet(ProjectViewlet, WriteGeoViewletBase):

    title = 'Location'

    map = ZopeTwoPageTemplateFile('map.pt')
    geocoding = ZopeTwoPageTemplateFile('geocoding.pt')
    latlong = ZopeTwoPageTemplateFile('latlong.pt')
    
    def render(self):
        return '\n'.join((self.geocoding(), self.latlong(), self.map()))

class MemberProfileViewlet(ReadGeoViewletBase):

    @property
    def geo_info(self):
        info = super(MemberProfileViewlet, self).geo_info
        # Override the static map image size. Ugh, sucks to have this in code.
        info['static_img_url'] = self.location_img_url(width=285, height=285)
        return info


    def _get_viewedcontent(self):
        # Find the member in the acquisition context.
        return self.__parent__.viewedmember()


class MemberProfileEditViewlet(MemberProfileViewlet, WriteGeoViewletBase):

    def remove_geo(self, *a, **b):
        # there's no public API for clearing a geolocation
        # in oc-geo or PGC, so we go a bit lowlevel here
        context = self._get_viewedcontent()
        annot = IAnnotations(context)
        georef = annot.get(ANNO_KEY, {})
        georef['geometryType'] = None
        georef['spatialCoordinates'] = None
        self.__parent__.add_status_message(u'Map location cleared')
        self.__parent__.redirect(self.context.absolute_url())
    
    def update(self):
        # this is a hack to plug a formhandler into a view
        # this hack is required by octopus
        view = self.__parent__
        geo_remove_action = Action("remove_geo", instance=self)
        view.actions["remove_geo"] = geo_remove_action


class GeoJSViewlet(object):

    """provides a <script> tag for pages that need geo-related js
    """

    sort_order = 0

    def __init__(self, context, request, view, manager):
        self.context = context
        self.request = request
        self.__parent__ = self.view = view
        self.manager = manager

    def update(self):
        pass

    def render(self):
        # We have a map key for each possible hostname in build.ini.
        url = self.request['ACTUAL_URL']
        # In python 2.5, this could be written as urlparse(url).hostname
        hostname = urlparse(url)[1].split(':')[0]
        # Google maps key for a domain can be used for any subdomain.
        # So we should register them for our domains, not subdomains.
        hostname = '.'.join(hostname.split('.')[-2:])
        # fassemblerconfigparser magically flattens the build.ini into
        # one big namespace, so we can just hope it'll find the
        # hostname in the google_maps_keys section... this works as
        # long as your hostname isn't something like # 'opencore_site_id'
        # ... Really this means our build.ini is getting a bit overloaded.
        config = getUtility(IProvideSiteConfig)
        key = config.get(hostname)
        if not key:
            warnings.warn("need a google maps key for %r" % hostname)
            return ''
        url = "http://maps.google.com/maps?file=api&v=2&key=%s" % key
        return '<script src="%s" type="text/javascript"></script>' % url
    
