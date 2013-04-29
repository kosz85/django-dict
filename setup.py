# -*- encoding: utf8 -*-
from setuptools import setup, find_packages

import os

setup(
    name="django-dict",
    version="0.2",
    url='https://github.com/kosz85/django-dict',
    download_url='',
    license='BSD',
    description="Django to dict toolkit",
    long_description=file(os.path.join(os.path.dirname(__file__),
                          'README.rst')).read(),
    author='Konrad Szymański',
    author_email='kosz85@o2.pl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=['todict'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
