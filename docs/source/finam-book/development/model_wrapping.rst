========================
Wrapping existing models
========================

This chapter explains the requirements for models to be coupled using FINAM,
potentially in languages other than Python.
Further, the procedure of wrapping a model into a FINAM `Component` is outlined.

The chapter focuses on simulation models with an internal time step.

Requirements
------------

Python extension/bindings
^^^^^^^^^^^^^^^^^^^^^^^^^

* The model must be accessible through a Python extension

Required functionality
^^^^^^^^^^^^^^^^^^^^^^

* The Python extension needs at least the following functionality:
  * Initialize the model (ideally an instance of the model)
  * Step the model

* Optionally, the Python extension can offer the following functionality:
  * Get data from the model
  * Set data in the model
  * Get the current simulation time of the model
  * Finalize the model

Preparing a model
-----------------

Python extension/bindings
^^^^^^^^^^^^^^^^^^^^^^^^^^^

See chapter :doc:`py-bindings` for details.

FINAM wrapper
^^^^^^^^^^^^^

See chapter :doc:`components` for a walk through of howto write a model wrapper.

The chapter Components describes how to write a model wrapper.