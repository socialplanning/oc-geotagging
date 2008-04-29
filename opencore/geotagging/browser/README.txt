-*- mode: doctest ;-*-

Geocoding views of opencore content
===================================

first some setup...

    >>> self.login(project_admin)
    >>> projects = portal.projects
    >>> proj = projects[project_name]
    >>> view = proj.restrictedTraverse('preferences')


Script tag viewlet
------------------

This provides a way to get the correct google maps javascript url for
this host.  XXX this relies on the built configuration; need to
mock up get_config.

    >>> jsviewlet = viewlets.GeoJSViewlet(view.context, view.request, view,
    ...                                   "irrelevant manager")
    >>> jsviewlet.render()
    '<script src="http://..." type="text/javascript"></script>'



Preferences view for Projects
------------------------------

We can wrap a project edit view in a geo-specific viewlet::

    >>> reader = viewlets.ProjectViewlet(view.context, view.request, view,
    ...                                   "irrelevant manager")

It implements an interface::

    >>> verify.verifyObject(geotagging.interfaces.IReadGeo, reader)
    True

Coordinates are empty when not set::

    >>> reader.geo_info.get('position-latitude')
    ''
    >>> reader.geo_info.get('position-longitude')
    ''

We have a ProjectEditViewlet that can be used to handle forms and
store new coords:

    >>> writer = viewlets.ProjectEditViewlet(view.context, view.request, view,
    ...                                       "irrelevant manager")

It implements these interfaces::

    >>> verify.verifyObject(geotagging.interfaces.IReadGeo, writer)
    True
    >>> verify.verifyObject(geotagging.interfaces.IWriteGeo, writer)
    True
    >>> verify.verifyObject(geotagging.interfaces.IReadWriteGeo, writer)
    True
    >>> writer.geo_info.get('position-latitude')
    ''
    >>> writer.geo_info.get('position-longitude')
    ''

If we save an empty form, nothing changes::

    >>> form = {}
    >>> info, changed = writer.save_coords_from_form(form)
    >>> changed
    []
    >>> writer.geo_info.get('position-latitude')
    ''
    >>> writer.geo_info.get('position-longitude')
    ''

You can set and then view coordinates::

    >>> writer.set_geolocation((11.1, -22.2))
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(view)
    >>> print writer.geo_info.get('position-latitude')
    11.1
    >>> print writer.geo_info.get('position-longitude')
    -22.2

Calling again with the same points makes no change:

    >>> writer.set_geolocation((11.1, -22.2))
    False

Our read-only viewlet can see the changes we've made::

    >>> reader.geo_info == writer.geo_info
    True


You can extract stuff from the form::

    >>> form = {'position-latitude': '10.0', 'position-longitude': '-20.0'}
    >>> info, changed = writer.get_geo_info_from_form(form)
    >>> info['position-latitude'] == float(form['position-latitude'])
    True
    >>> info['position-longitude'] == float(form['position-longitude'])
    True

You can also pass in a string; if there's no coordinates passed, we
use a remote service to look them up from this string.  We're using a
mock so we don't actually hit google on every test run::

    >>> utils.clear_status_messages(view)
    >>> form.clear()
    >>> form['position-text'] = "mock address"
    >>> form['location'] = 'mars'
    >>> info, changed = writer.save_coords_from_form(form)
    Called ....geocode('mock address')
    >>> utils.clear_all_memos(view)  # XXX ugh, wish this wasn't necessary.
    >>> print writer.geo_info.get('position-latitude')
    12.0
    >>> print writer.geo_info.get('position-longitude')
    -87.0


Our read-only viewlet can see the changes we've made::

    >>> reader.geo_info == writer.geo_info
    True

But we let the content's own form handlers handle everything else; we
might want to revisit this, it feels kind of schizo.  For now, this
means that other things in the request aren't saved unless we invoke
the form handler, not just our wrapper viewlet.

    >>> writer.geo_info['position-text'] == form['position-text']
    False
    >>> writer.geo_info['location'] == form['location']
    False

We can submit to the preferences view and, since it includes our
writer viewlet, our information gets stored, including the usual
archetypes "location" field, for use as a human-readable place name::

    >>> view = proj.restrictedTraverse('preferences')
    >>> utils.clear_status_messages(view)
    >>> view.request.form.clear()
    >>> view.request.form.update({'location': "oceania", 'update': True,
    ...     'project_title': 'IGNORANCE IS STRENGTH',
    ...     'position-text': 'mock address'})

    >>> view.handle_request()
    Called ....geocode('mock address')
    >>> utils.get_status_messages(view)
    [...u'The location has been changed.'...]
    >>> view.context.getLocation()
    'oceania'
    >>> utils.clear_all_memos(view)
    >>> reader = viewlets.ProjectViewlet(view.context, view.request, view,
    ...                                  "irrelevant manager")

    >>> reader.geo_info.get('position-text')  # saved now.
    'mock address'

The viewlet includes a bunch of convenient geo-related stuff for UIs::

    >>> sorted(reader.geo_info.keys())
    ['is_geocoded', 'location', 'position-latitude', 'position-longitude', 'position-text', 'static_img_url']
    >>> reader.geo_info['is_geocoded']
    True

    >>> reader.geo_info['location']
    'oceania'

    >>> round(reader.geo_info['position-latitude'])
    12.0
    >>> round(reader.geo_info['position-longitude'])
    -87.0

    >>> reader.geo_info['position-text']
    'mock address'
    >>> reader.geo_info['static_img_url']
    'http://maps.google.com/mapdata?latitude_e6=12000000&longitude_e6=4207967296&w=500&h=300&zm=9600&cc='

clean up...
    >>> view.request.form.clear()
