.. post:: 14 Sep, 2023
    :tags: announcement
    :category: Release
    :author: Martin Lange
    :excerpt: 2

==================
FINAM 0.5 released
==================

Around half a year after the :ref:`release of FINAM 0.4.0 <release-0-4-0>`,
we are pleased to announce version 0.5.

What's new?
-----------

This release is focussed on supporting masked data and on improved grid usability.

Masked array support
^^^^^^^^^^^^^^^^^^^^

FINAM now supports masked data.
Masked data, especially on structured grids, is particularly useful for handling simulation domains
that only fill parts of their bounding box.

FINAM uses :mod:`numpy` :class:`ma.MaskedArray <numpy.ma.MaskedArray>` for representing masked data.
As :class:`ma.MaskedArray <numpy.ma.MaskedArray>` is a sub-class of :class:`numpy.ndarray`,
developers can work with it like with any unmasked data in most cases.
E.g., arithmetic operations are available as usual, but automatically ignore masked values.

See book chapter :doc:`/finam-book/development/data_metadata` for more details.

Grid compatibility
^^^^^^^^^^^^^^^^^^

FINAM now detects compatible grids and converts them automatically during data transfer between components.

Grids are compatible if the transformation between them can be performed using simple operations like axis reversal or transposition.
In these cases, there is no expensive regridding required. FINAM 0.5 detects the required transformations and performs them automatically in all receiving inputs.

External modules
^^^^^^^^^^^^^^^^

With the release of FINAM 0.5, several external modules got their first official releases:

* `finam-netcdf <https://finam.pages.ufz.de/finam-netcdf/>`_ for NetCDF reader and writer components
* `finam-plot <https://finam.pages.ufz.de/finam-plot/>`_ for live plotting components to visualize time series and grids
* `finam-regrid <https://finam.pages.ufz.de/finam-regrid/>`_ for regridding adapters based on `ESMPy <https://earthsystemmodeling.org/esmpy/>`_
* `finam-graph <https://finam.pages.ufz.de/finam-graph/>`_ for visualizing FINAM coupling compositions

For a full list of changes, see the :doc:`/about/changelog`.

The :doc:`/about/authors`.
