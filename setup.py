# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='sapns',
    version='0.4',
    description='Web platform by Ender',
    author='León Domingo',
    author_email='leon.domingo@ender.es',
    url='http://www.ender.es',
    install_requires=[
        "TurboGears2 >= 2.2.0",
        "Genshi",
        "Jinja2",
        "zope.sqlalchemy >= 0.4",
        "repoze.tm2 >= 1.0a5",
        "sqlalchemy",
        "sqlalchemy-migrate",
        "repoze.who",
        "repoze.who-friendlyform >= 1.0.4",
        "tgext.admin >= 0.5.1",
        "repoze.who.plugins.sa",
        "tw2.forms",
        "Neptuno2",
        "argparse",
        "pymongo",
    ],
    setup_requires=['PasteScript >= 1.7'],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2', 'tg.devtools'],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['WebTest',
                   'nosetests',
                   'coverage',
                   'wsgiref'
                   ],
    package_data={'sapns': ['i18n/*/LC_MESSAGES/*.mo',
                            'templates/*/*',
                            'public/*/*']},
    message_extractors={'sapns': [
            ('**.py', 'python', None),
            ('templates/**.html', 'jinja2', None),
            ('templates/**.js', 'jinja2', None),
            ('public/**', 'ignore', None)]},

    entry_points="""
    [paste.app_factory]
    main = sapns.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
    dependency_links=[
        "http://tg.gy/220"
        ],
    zip_safe=False
)