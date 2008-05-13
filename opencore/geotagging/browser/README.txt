-*- mode: doctest ;-*-

Geocoding views of opencore content
===================================

first some setup...

    >>> self.login(project_admin)
    >>> projects = portal.projects
    >>> proj = projects[project_name]
    >>> prefs_view = proj.restrictedTraverse('preferences')


Script tag viewlet
------------------

This provides a way to get the correct google maps javascript url for
this host.

    >>> getUtility(IProvideSiteConfig)._set('nohost', 'bogusKey')
    >>> jsviewlet = viewlets.GeoJSViewlet(prefs_view.context,
    ...     prefs_view.request, prefs_view, "irrelevant manager")
    >>> jsviewlet.render()
    '<script src="http://...&key=bogusKey..." type="text/javascript"></script>'



Preferences view for Projects
------------------------------

We can wrap a project edit view in a geo-specific viewlet::

    >>> reader = viewlets.ProjectViewlet(prefs_view.context,
    ...    prefs_view.request, prefs_view, "irrelevant manager")

It implements an interface::

    >>> verify.verifyObject(geotagging.interfaces.IReadGeo, reader)
    True

Coordinates are empty when not set::

    >>> reader.geo_info.get('position-latitude')
    ''
    >>> reader.geo_info.get('position-longitude')
    ''
    >>> print reader.get_geolocation()
    None
    >>> print reader.is_geocoded()
    False
    >>> reader.location_img_url()
    ''


We have a ProjectEditViewlet that can be used to handle forms and
store new coords:

    >>> writer = viewlets.ProjectEditViewlet(prefs_view.context,
    ...     prefs_view.request, prefs_view, "irrelevant manager") 

It implements these interfaces::

    >>> verify.verifyObject(geotagging.interfaces.IReadGeo, writer)
    True
    >>> verify.verifyObject(geotagging.interfaces.IWriteGeo, writer)
    True
    >>> verify.verifyObject(geotagging.interfaces.IReadWriteGeo, writer)
    True

If we save an empty form, nothing changes::

    >>> writer.geo_info.get('position-latitude')
    ''
    >>> writer.geo_info.get('position-longitude')
    ''
    >>> form = {}
    >>> info, changed = writer.save_coords_from_form(form)
    >>> changed
    []
    >>> writer.geo_info.get('position-latitude')
    ''
    >>> writer.geo_info.get('position-longitude')
    ''

You can set and then view coordinates::

    >>> writer.set_geolocation((-22.2, 11.1))  # longitude first
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(prefs_view)
    >>> print writer.geo_info.get('position-latitude')
    11.1
    >>> print writer.geo_info.get('position-longitude')
    -22.2
    >>> writer.is_geocoded(), reader.is_geocoded()
    (True, True)


Calling again with the same points makes no change:

    >>> writer.set_geolocation((-22.2, 11.1))
    False

Our read-only viewlet can see the changes we've made::

    >>> reader.geo_info == writer.geo_info
    True
    >>> reader.location_img_url()
    'http://maps.google.com/...'
    >>> reader.get_geolocation() == (-22.2, 11.1, 0.0)
    True


You can extract stuff from the form without saving::

    >>> form = {'position-latitude': '10.0', 'position-longitude': '-20.0'}
    >>> info, changed = writer.get_geo_info_from_form(form)
    >>> info['position-latitude'] == float(form['position-latitude'])
    True
    >>> info['position-longitude'] == float(form['position-longitude'])
    True

No change with an empty form::

    >>> prefs_view.request.form.clear()
    >>> info, changed = writer.get_geo_info_from_form()
    >>> info == writer.geo_info
    True
    >>> changed
    []

get_geo_info_from_form has no side effects:

    >>> prefs_view.request.form.clear()
    >>> reader.get_geolocation() == (-22.2, 11.1, 0.0)
    True

The request overrides the values returned by get_geo_info_from_form,
but not geo_info:

    >>> old_info = reader.geo_info.copy()
    >>> prefs_view.request.form.update({'location': 'nunya bizness',
    ...     'position-latitude': 1.2, 'position-longitude': 3.4,
    ...     'position-text': 'my house',  'static_img_url': 'IGNORED',
    ...     'maps_script_url': 'IGNORED'})
    >>> info, changed = writer.get_geo_info_from_form()
    >>> info == old_info
    False
    >>> info['location']
    'nunya bizness'
    >>> print info['position-latitude'], info['position-longitude']
    1.2 3.4
    >>> info['position-text']
    'my house'


You can also pass in a string; if there's no coordinates passed, we
use a remote service to look them up from this string.  We're using a
mock so we don't actually hit google on every test run::

    >>> utils.clear_status_messages(prefs_view)
    >>> form.clear()
    >>> form['position-text'] = "mock address"
    >>> form['location'] = 'mars'
    >>> info, changed = writer.save_coords_from_form(form)
    Called ....geocode('mock address')
    >>> utils.clear_all_memos(prefs_view)  # XXX ugh, wish this wasn't necessary.
    >>> print writer.geo_info.get('position-latitude')
    12.0
    >>> print writer.geo_info.get('position-longitude')
    -87.0


Our read-only viewlet can see the changes we've made::

    >>> reader.geo_info == writer.geo_info
    True

But we let the content's own form handlers handle everything else.
XXX We might want to revisit this, it feels kind of schizo.
For now, this means that other things in the request aren't saved
unless we invoke the form handler, not just our wrapper viewlet.

    >>> writer.geo_info['position-text'] == form['position-text']
    False
    >>> writer.geo_info['location'] == form['location']
    False

We can submit to the preferences view and, since it includes our
writer viewlet and calls its save method, our information gets stored;
including the usual archetypes "location" field, for use as a
human-readable place name::

    >>> prefs_view = proj.restrictedTraverse('preferences')
    >>> utils.clear_status_messages(prefs_view)
    >>> prefs_view.request.form.clear()
    >>> prefs_view.request.form.update({'location': "oceania", 'update': True,
    ...     'project_title': 'IGNORANCE IS STRENGTH',
    ...     'position-text': 'mock address'})

    >>> prefs_view.handle_request()
    Called ....geocode('mock address')
    >>> utils.get_status_messages(prefs_view)
    [...u'The location has been changed.'...]
    >>> prefs_view.context.getLocation()
    'oceania'
    >>> utils.clear_all_memos(prefs_view)
    >>> reader = viewlets.ProjectViewlet(prefs_view.context,
    ...     prefs_view.request, prefs_view, "irrelevant manager")

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
    >>> prefs_view.request.form.clear()

Create view for Projects
------------------------

    >>> self.login(project_admin)
    >>> createview = projects.restrictedTraverse("create")

Looking up geo info on the add view gives us nothing much useful,
because the project doesn't exist yet::

    >>> reader = viewlets.ProjectViewlet(createview.context,
    ...    createview.request, createview, 'blah')
    >>> reader.geo_info['is_geocoded']
    False

But if you actually submit the project create form, you can see the
result on the edit view::

    >>> createview.request.form.update({'project_title': 'A geolocated project!',
    ...    'projid': 'testgeo', 'workflow_policy': 'medium_policy',
    ...    'position-latitude': '33.33', 'position-longitude': '44.44'})
    >>> out = createview.handle_request()
    >>> createview.errors
    {}
    >>> prefs_view = projects.restrictedTraverse('testgeo/preferences')
    >>> utils.clear_all_memos(prefs_view)
    >>> reader = viewlets.ProjectViewlet(prefs_view.context,
    ...     prefs_view.request, prefs_view, "irrelevant manager")
    >>> print reader.geo_info['position-latitude']
    33.33
    >>> print reader.geo_info['position-longitude']
    44.44

Clean that one up...

    >>> projects.manage_delObjects(['testgeo'])
    >>> prefs_view.request.form.clear()

XXX Add tests for publically available views of projects,
once they include geo info.

Feeds for Projects
------------------


These are all anonymously viewable::

    >>> self.logout()

The Projects collection can be adapted to a sequence of dictionaries
suitable for building a georss view::

    >>> view = projects.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    1
    >>> info = info[0]  #XXX what order do they come back in?

    Note that coords_georss is latitude-longitude, so you get them
    back in the reverse order:

    >>> info['coords_georss']
    '12.000000 -87.000000'
    >>> info['geometry']['type']
    'Point'
    >>> info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['hasLineString']
    0
    >>> info['hasPoint']
    1
    >>> info['hasPolygon']
    0
    >>> info['id'] == project_name
    True
    >>> print info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['properties']['description']
    'No description'
    >>> info['properties']['link']
    'http://nohost/plone/projects/p3'
    >>> info['properties']['title']
    'IGNORANCE IS STRENGTH'

(Unfortunately it's hard to assert much about dates...  it should
look iso8601-ish.)

    >>> info['properties']['updated']
    '...-...-...T...:...:...'
    >>> info['properties']['created'] == info['properties']['created']
    True


You can also adapt to a view suitable for building kml::

    >>> view = projects.restrictedTraverse('@@geo')
    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> info = info[0]

    Note that coords_kml is of the form longitude,latitude,z.

    >>> info['coords_kml']
    '-87.000000,12.000000,0.000000'
    >>> info['geometry']['type']
    'Point'
    >>> print info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['hasLineString']
    0
    >>> info['hasPoint']
    1
    >>> info['hasPolygon']
    0
    >>> info['id'] == project_name
    True
    >>> info['properties']['title']
    'IGNORANCE IS STRENGTH'

The projects georss view is exposed by a separate view that generates
xml.

    >>> feedview = projects.restrictedTraverse('@@georss')
    >>> xml = get_response_output(feedview)
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    Status: 200 OK...
    <?xml...
    <feed
    ...xmlns="http://www.w3.org/2005/Atom"...
    <title>Projects</title>
    <link rel="self" href="http://nohost/plone/projects"/>...
    <entry>
    <title>IGNORANCE IS STRENGTH</title>...
    <id>http://nohost/plone/projects/p3</id>...
    <georss:where><gml:Point>
    <gml:pos>12.000000 -87.000000</gml:pos>
    </gml:Point>...


And a separate view that generates kml markup::

    >>> feedview = projects.restrictedTraverse('@@kml')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml...
    <kml xmlns="http://earth.google.com/kml/2.1">
    <Document>...
    <name>Projects</name>...
    <Placemark>
    <name>IGNORANCE IS STRENGTH</name>
    <description>...
    <p>URL:
    <a href="http://nohost/plone/projects/p3">http://nohost/plone/projects/p3</a>...
    <Point>
    <coordinates>-87.000000,12.000000,0.000000</coordinates>
    </Point>...
    </kml>


Profile edit views for Members
------------------------------

We can wrap a profile edit view in a geo-specific viewlet::

    >>> people = portal.people
    >>> m1 = people.m1
    >>> self.login('m1')
    >>> prof_view = m1.restrictedTraverse('@@profile-edit')
    >>> prof_view.request.form.clear()
    >>> reader = viewlets.MemberProfileViewlet(prof_view.context,
    ...     prof_view.request, prof_view, 'irrelevant')
    >>> pprint(reader.geo_info)
    {'is_geocoded': False,
     'location': '',
     'position-latitude': '',
     'position-longitude': '',
     'position-text': '',
     'static_img_url': ''}
    
We have an edit viewlet that can be used to handle forms and
store new coords::

    >>> writer = viewlets.MemberProfileEditViewlet(prof_view.context,
    ...     prof_view.request, prof_view, "irrelevant manager") 

It implements these interfaces::

    >>> verify.verifyObject(geotagging.interfaces.IReadGeo, writer)
    True
    >>> verify.verifyObject(geotagging.interfaces.IWriteGeo, writer)
    True
    >>> verify.verifyObject(geotagging.interfaces.IReadWriteGeo, writer)
    True

If we save an empty form, nothing changes::

    >>> writer.geo_info.get('position-latitude')
    ''
    >>> writer.geo_info.get('position-longitude')
    ''
    >>> form = {}
    >>> info, changed = writer.save_coords_from_form(form)
    >>> changed
    []
    >>> writer.geo_info.get('position-latitude')
    ''
    >>> writer.geo_info.get('position-longitude')
    ''

You can set and then view coordinates::

    >>> writer.set_geolocation((-77.77, 88.88))
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(prof_view)
    >>> print reader.geo_info.get('position-latitude')
    88.88
    >>> print reader.geo_info.get('position-longitude')
    -77.77
    >>> reader.get_geolocation() == (reader.geo_info['position-longitude'], reader.geo_info['position-latitude'], 0.0)
    True

Submitting the profile edit form updates everything, and we get a
static image url now::

    >>> prof_view.request.form.update({'position-latitude': 45.0,
    ...  'position-longitude': 0.0, 'location': 'somewhere', })
    >>> redirected = prof_view.handle_form()
    >>> utils.clear_all_memos(prof_view)
    >>> pprint(reader.geo_info)
    {'is_geocoded': True,
     'location': 'somewhere',
     'position-latitude': 45.0,
     'position-longitude': 0.0,
     'position-text': '',
     'static_img_url': 'http://...'}

Submitting the form with position-text should cause the (mock)
geocoder to be used::

    >>> prof_view = m1.restrictedTraverse('@@profile-edit')
    >>> prof_view.request.form.clear()
    >>> reader = viewlets.MemberProfileViewlet(prof_view.context,
    ...     prof_view.request, prof_view, 'irrelevant')
    >>> prof_view.request.form.update({'position-text': 'atlantis',
    ...     'location': 'somewhere underwater', })
    >>> redirected = prof_view.handle_form()
    Called ...geocode('atlantis')

    >>> utils.clear_all_memos(prof_view)  # XXX Ugh, make this unnecessary.
    >>> pprint(reader.geo_info)
    {'is_geocoded': True,
     'location': 'somewhere underwater',
     'position-latitude': 12.0,
     'position-longitude': -87.0,
     'position-text': 'atlantis',
     'static_img_url': 'http://...'}


The public profile view should show the same data::

    >>> self.logout()
    >>> pview = m1.restrictedTraverse('@@profile')
    >>> pview.request.form.clear()
    >>> pviewlet = viewlets.MemberProfileViewlet(pview.context, pview.request,
    ...                                 pview, "irrelevant manager")
    >>> pviewlet.geo_info == reader.geo_info
    True
    

Request values affect get_geo_info_from_form but not geo_info:

    >>> old_info = reader.geo_info.copy()
    >>> prof_view.request.form.update({'position-latitude': 45.0,
    ...  'position-longitude': 0.0, 'location': 'somewhere', })

    >>> info, changed = writer.get_geo_info_from_form()
    >>> info == old_info
    False
    >>> sorted(changed)
    ['location', 'position-latitude', 'position-longitude', 'static_img_url']
    >>> pprint(info)
    {'is_geocoded': True,
     'location': 'somewhere',
     'position-latitude': 45.0,
     'position-longitude': 0.0,
     'position-text': 'atlantis',
     'static_img_url': 'http://maps...'}


Feeds for Members
------------------

A bit of setup here to avoid depending on previous tests, yuck::

    >>> self.login('m1')
    >>> edit = m1.restrictedTraverse('profile-edit')
    >>> edit.request.form.clear()
    >>> edit.request.form.update({'location': 'nowhere', 'position-latitude': -66.0,
    ...      'position-longitude': 55.0})

    >>> redirected = edit.handle_form()


First try the views that generate info, should be public::

    >>> self.logout()
    >>> view = people.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    1
    >>> pprint(info)
    [{'coords_georss': '-66.000000 55.000000',
      'geometry': {'type': 'Point', 'coordinates': (55.0, -66.0, 0.0)},
      'hasLineString': 0,
      'hasPoint': 1,
      'hasPolygon': 0,
      'id': 'm1',
      'properties': {...}}]
    >>> pprint(info[0]['properties'])
    {'created': '...-...-...T...:...:...',
     'description': 'No description',
     'language': '',
     'link': 'http://nohost/plone/people/m1',
     'location': 'nowhere',
     'title': 'Member One',
     'updated': '...-...-...T...:...:...'}


And similar info for generating kml::

    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> pprint(info)
    [{'coords_kml': '55.000000,-66.000000,0.000000',...


Now the actual georss xml feed::

    >>> feedview = portal.people.restrictedTraverse('@@georss')
    >>> xml = get_response_output(feedview)
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml version="1.0"...
    <title>People</title>
    <link rel="self" href="http://nohost/plone/people"/>...
    <id>http://nohost/plone/people</id>
    <entry>
    <title>Member One</title>...
    <updated>...-...-...T...:...:...</updated>...
    <georss:where><gml:Point>
    <gml:pos>-66.000000 55.000000</gml:pos>
    </gml:Point>...


Now the actual kml feed::

    >>> feedview = portal.people.restrictedTraverse('@@kml')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml...
    <kml xmlns="http://earth.google.com/kml/2.1">
    <Document>...
    <name>People</name>...
    <Placemark>
    <name>Member One</name>
    <description>...
    <p>URL:
    <a href="http://nohost/plone/people/m1">http://nohost/plone/people/m1</a>...
    <Point>
    <coordinates>55.000000,-66.000000,0.000000</coordinates>
    </Point>...
    </kml>
