from geopy.geocoders import Google
from Products.PleiadesGeocoder.interfaces import IGeoItemSimple

def geolocate_content(brains):
    geocoder = Google(resource='maps')
    
    for item in brains:
        content = item.getObject()
        location = content.getLocation()

        if not location: continue
        
        results = geocoder.geocode(location, exactly_one=False)
        geolocation = None

        for geolocation in results:
            name, latlon = geolocation
            content = IGeoItemSimple(content)
            content.setGeoInterface('Point', latlon)
            break

mt = app.openplans.membrane_tool
people = mt(review_state='public')
geolocate_content(people)

import transaction
transaction.commit()
