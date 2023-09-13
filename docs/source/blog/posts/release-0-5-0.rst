.. post:: 12 Sep, 2023
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

This release is focussed on supporting masked data.

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

For a full list of changes, see the :doc:`/about/changelog`.

The :doc:`/about/authors`.
