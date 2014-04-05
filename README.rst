.. image:: https://travis-ci.org/pavlov99/tabtool.png
    :target: https://travis-ci.org/pavlov99/tabtool
    :alt: Build Status

.. image:: https://coveralls.io/repos/pavlov99/tabtool/badge.png
    :target: https://coveralls.io/r/pavlov99/tabtool
    :alt: Coverage Status

.. image:: https://pypip.in/v/tabtool/badge.png
    :target: https://crate.io/packages/tabtool
    :alt: Version

.. image:: https://pypip.in/d/tabtool/badge.png
    :target: https://crate.io/packages/tabtool
    :alt: Downloads

Documentation: http://tabtool.readthedocs.org

Install
-------

.. code-block:: python

    pip install tabtool

Tests
-----

.. code-block:: python

    tox

Preface
-------

Utils for tab separated files management were developed in `Yandex <http://yandex.com>`_.
Core functionality was designed and implemented by Alex Akimov.
I was working as developer there and used utils.
During that period I decided to use tab separated files format in `pmll <https://github.com/pavlov99/pmll>`_ library to handle datasets for machine learning.
After I left Yandex, I asked team to open source package.
Guys agreed, but did not do it.
As far as I needed some functionality, I started my own implementation of simple package version.
Then `Andrey Fyodorov <https://github.com/andreifyodorov>`_ (developer from the team) released `tabkit <https://github.com/andreifyodorov/tabkit>`_ version (very similar to one we had).
I dont know, whether tabkit code is supported or not, if supported, who is responsible for that.
I would like to continue development with Alex Akimov, if he would like to join.
As of now, there is implementation I write according to pep standards with python2 and python3 support.
