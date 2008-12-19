from setuptools import setup, find_packages

version = '0.3'

setup(name='oc-geotag',
      version=version,
      description="Geotagging for opencore content",
      long_description='',
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Plone",
        ],
      keywords='openplans openplans.org topp geotagging geocoding',
      author='The Open Planning Project',
      author_email='opencore-dev@lists.openplans.org',
      url='http://openplans.org/projects/opencore',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['opencore'],
      include_package_data=True,
      zip_safe=False,
      dependency_links=[
          'https://svn.openplans.org/svn/vendor/geopy/openplans/dist',
      ],
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'geopy==0.93-20071130',  # forces our vendor branch.
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
