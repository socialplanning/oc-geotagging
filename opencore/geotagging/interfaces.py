from zope.interface import Interface
from zope.interface import Attribute

class IReadGeo(Interface):
    """View for using OpenCore content with geotagging.
    """

    def get_geolocation():
        """Get the current coordinates of the context.
        Output as (longitude, latitude, z)"""

    def location_img_url():
        """
        Used for non-ajax UI to get a static map image for the context's
        location.
        """

    def is_geocoded():
        """Boolean. True if we can get coordinates, false otherwise.
        """

    geo_info = Attribute(
        """Returns a single dict containing all the interesting stuff.
        XXX more doc
        """
        )
        


class IWriteGeo(Interface):

    request = Attribute(
        'HTTP request object; making the access to the '
        'HTTP form explicit')
    
    def get_geo_info_from_form(old_info=None):
        """
        Returns a dict and a list: (info, changed), Just like
        utils.update_info_from_form (to which it delegates), but the
        form is retrieved from the HTTP request rather than being
        passed in.

        You can pass an old_info if you're writing an add view and the
        content you're geotagging doesn't exist yet.

        No side effects, just returns stuff.
        """

    def set_geolocation(coords):
        """Store coordinates on the context, as a tuple of (lon, lat, z).
        (the z coord is optional; default is 0.0).

        If a change is made, return True; else return False.
        """

    def save_coords_from_form():
        """Does a lookup just like get_geo_info_from_form, and saves
        the resulting coordinates if necessary."""

class IReadWriteGeo(IReadGeo, IWriteGeo):
    """both read + write.
    """
