from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from opencore.geotagging.testing import readme_setup, readme_teardown
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
from opencore.testing.setup import hook_setup
from zope.testing import doctest
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")


def test_suite():
    from Products.PloneTestCase import setup
    from opencore.project.browser.base import ProjectBaseView
    from opencore.member.browser.view import ProfileView
    from pprint import pprint
    from Products.PleiadesGeocoder.interfaces import IGeoItemSimple, IGeoFolder,\
         IGeoreferenceable, IGeoAnnotatableContent, IGeoserializable, \
         IGeoserializableMembersFolder
    from opencore.geotagging.interfaces import IReadGeo, IWriteGeo, IReadWriteGeo
    ZopeTestCase.installProduct('PleiadesGeocoder')
    setup.setupPloneSite()

    globs = locals()

    config = dtf.ZopeDocFileSuite('configuration.txt',
                                  optionflags=optionflags,
                                  package='opencore.geotagging',
                                  test_class=OpenPlansTestCase,
                                  globs=globs,
                                  setUp=hook_setup,
                                  layer=test_layer
                                  )
    utilsunit = doctest.DocTestSuite('opencore.geotagging.utils',
                                     optionflags=optionflags)
    return unittest.TestSuite((utilsunit,
                               config,
                               ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
