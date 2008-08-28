from geopy.geocoders import Google
from Products.PleiadesGeocoder.interfaces import IGeoItemSimple

geocoder = Google(resource='maps')
    
mt = app.openplans.membrane_tool
people = mt(review_state='public')
n = 0
for item in people:
    content = item.getObject()
    location = content.getLocation()

    if not location: continue
    
    results = geocoder.geocode(location, exactly_one=False)

    for geolocation in results:
        # take the first location we get if there are many results
        name, latlon = geolocation
        # doReverse = True
        x,y = latlon
        lonlat = y,x
        geocontent = IGeoItemSimple(content)
        geocontent.setGeoInterface('Point', lonlat)
        print '%s -> %s %s' % (content.Title(), name, str(lonlat))
        n += 1
        break


import transaction
transaction.get().note('updated locations for %s users' % n)
transaction.commit()
