from setuptools import setup

import survey


setup(
    name = survey.__name__,
    version = survey.__version__,
    author = survey.__author__,
    author_email = survey.__email__,
    license = survey.__license__,
    description = survey.__doc__.splitlines()[0],
    long_description = open('README.rst').read(),
    url = 'http://github.com/goabout/survey',
    packages = ['survey'],
    include_package_data = True,
    zip_safe = False,
    platforms = ['all'],
    test_suite = 'tests',
    entry_points = {
        'console_scripts': [
            'survey-send = survey.worker:main',
        ],
    },
    install_requires = [
        'mandrill',
        'dougrain',
        'requests',
        'gdata',
        'requests-oauthlib',
    ],
)
