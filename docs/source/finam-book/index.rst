==========
FINAM Book
==========

FINAM is an open-source component-based model coupling framework for environmental models.
It aims at enabling bi-directional online couplings of models for different compartments like geo-, hydro-, pedo- and biosphere.

.. image:: images/logo_large.svg
    :alt: FINAM Logo
    :class: dark-light p-2
    :width: 300px
    :target: https://finam.pages.ufz.de

The framework is built in Python, with well-defined interfaces for data exchange.
This approach allows for coupling of models irrespective of their internal structure, architecture or programming language.


* :doc:`about` -- The purpose of this book, and how to read it.
* :doc:`principles/index` -- Explains basic principles of the FINAM framework that are of interest for users as well as developers.
* :doc:`usage/index` -- Guide for users that aim at coupling existing models.
* :doc:`development/index` -- Guide for developers on how to prepare models for FINAM, and how to implement adapters.
* :doc:`cookbook/index` -- Short recipes demonstrating how to solve specific tasks with and for FINAM.

.. toctree::
    :hidden:
    :maxdepth: 1

    self
    quickstart

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Sections

    about
    principles/index
    usage/index
    development/index
    cookbook/index
