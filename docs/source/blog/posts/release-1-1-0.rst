.. post:: 04 Jun, 2026
    :tags: announcement
    :category: Release
    :author: Sebastian Müller
    :excerpt: 2

==================
FINAM 1.1 released
==================

FINAM 1.1 is a focused release that improves mask handling, grid conversion,
and adapter behavior after the first stable FINAM 1.0 release.

What's new?
-----------

Mask and grid adapters
^^^^^^^^^^^^^^^^^^^^^^

This release adds new adapters for common data preparation tasks:

- :class:`.adapters.Masking` and :class:`.adapters.UnMasking` for explicit
  mask handling in couplings.
- :class:`.adapters.Clip` for clipping grid data to spatial bounds.
- :class:`.adapters.ToCRS` for converting grid coordinates to another
  coordinate reference system.
- :class:`.adapters.ToUnstructured` for converting structured grids to
  unstructured grids.

Together, these adapters make it easier to prepare data directly in a FINAM
coupling setup, especially when components use different spatial domains or
coordinate reference systems.

Improved metadata handling
^^^^^^^^^^^^^^^^^^^^^^^^^^

FINAM 1.1 improves the way mask and grid metadata is exchanged through inputs,
outputs, and adapters. The :class:`.components.WeightedSum` component now
supports masks, and the base :class:`.adapters.Callback` and
:class:`.adapters.Scale` adapters gained unit handling.

The release also adds :func:`.data.equal_crs` and automatic axis attributes
from CRS information, making CRS-aware grid handling more robust.

Bug fixes
^^^^^^^^^

Several fixes improve reliability for regridding and compatible grid
transformations:

- Regridding adapters now propagate masks more reliably.
- CRS transformations keep axis order stable.
- Compatible grid transformations handle multi-entry data correctly.
- CRS-derived axis attributes are generated in the correct order.
- Compatibility with newer :mod:`numpy` versions was restored for reshaping
  interpolator data.

Documentation
^^^^^^^^^^^^^

The documentation includes updated examples and links, plus new blog posts on
the FINAM 1.0 release and on model-code changes for coupling with FINAM.

For a full list of changes, see the :doc:`/about/changelog`.

The :doc:`/about/authors`.
