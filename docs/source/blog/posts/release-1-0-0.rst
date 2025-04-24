.. post:: 24 Apr, 2025
    :tags: announcement
    :category: Release
    :author: Sebastian Müller
    :excerpt: 2

==================
FINAM 1.0 released
==================

We are delighted to announce the first stable release of FINAM: Version 1.0 🎉

FINAM is an open-source, component-based model coupling framework designed for environmental modeling. It enables seamless, bi-directional online coupling of models across different environmental compartments such as geo-, hydro-, pedo-, and biosphere.

What's new?
-----------

This landmark release provides a robust foundation for environmental model integration, including substantial improvements, richer metadata handling, enhanced grid management, and extensive masking capabilities.

Breaking changes
^^^^^^^^^^^^^^^^

Several significant API refinements ensure clarity and long-term stability:

- Submodule ``modules`` renamed to :mod:`.components` for consistency.
- Argument ``modules`` renamed to ``components`` in :class:`.Composition`.
- Components now implement method ``_next_time`` instead of the ``next_time`` property.
- Fields in :class:`.Composition`, :class:`.Input`, and :class:`.Output` are now private; access via properties.
- Composition metadata restructured with separate sub-dictionaries for components and adapters.
- Updates to :class:`.Info` new optional init-args, changed signature for :meth:`.Info.accepts`, and simplified metadata checks.
- Extended flexibility in grid handling (``data_shape``, support for variable dimensions).

New features
^^^^^^^^^^^^

FINAM 1.0 introduces powerful new capabilities:

- Default metadata for components and adapters, easily extendable.
- Enhanced Grid class providing detailed cell connectivity metadata compatible with ESMF and VTK.
- New grid tools (``get_cells_matrix``, ``INV_VTK_TYPE_MAP``, ``VTK_CELL_DIM``) for improved interoperability.
- Advanced grid reuse and type casting (including ``copy`` method, improved location handling, and additional casting options).
- Enhanced masking support with :any:`Mask` enum (:any:`Mask.FLEX`, :any:`Mask.NONE`), integrated masking via :func:`.data.prepare`, and robust mask handling in regridding adapters (:class:`.adapters.RegridNearest`, :class:`.adapters.RegridLinear`).
- Improved adapter introspection through the new ``in_info`` property.

Bug fixes
^^^^^^^^^

Significant reliability enhancements:

- Corrected 3D structured grid cell generation, resolving issues with negative volumes.
- Compatibility restored with recent versions of :mod:`pint`.
- Documentation clarity and consistency improvements.

Documentation
^^^^^^^^^^^^^

The documentation has been significantly expanded:

- New detailed chapter on composition, component, and adapter metadata.
- Clear examples demonstrating new grid and masking features.
- Updated API reference reflecting recent changes.

Resources
^^^^^^^^^

- FINAM homepage: https://finam.pages.ufz.de
- FINAM documentation: https://finam.pages.ufz.de/finam/
- FINAM source code: https://git.ufz.de/FINAM/finam
- FINAM GitLab group: https://git.ufz.de/FINAM

For a full list of changes, see the :doc:`/about/changelog`.

The :doc:`/about/authors`.
