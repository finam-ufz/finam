========================
Wrapping existing models
========================

This chapter explains the requirements for models to be coupled using FINAM,
potentially in languages other than Python.
Further, the procedure of wrapping a model into a FINAM `Component` is outlined.

The chapter focuses on simulation models with an internal time step.

Python extension/bindings
-------------------------

The model must be accessible through a Python extension.
For ways to create Python bindings for models in different languages, see :doc:`py-bindings`.

Required functionality
----------------------

The Python extension needs at least the following functionality:

* **Create a model instance / object**.
  This should return the model as a Pyhon object, or a handle for use with the other functions.
* **Initialize the model.**
  Sets up the model, potentially with information about the model domain and parameters.
  In the most simple case, it initializes the model from a setup file that is processed internally.
* **Step/update the model.** Progresses the model by one time step.

This is sufficient to run the model as a FINAM component.
To allow for exchanging data with other components, at least one of the following is required:

* **Get data from the model.**
  Extract a state variable or parameter from the model instance, and prepare it as :class:`numpy.ndarray`, wrapped in :class:`pint.Quantity`.
  Exchange with other components must use one of FINAM's grid types.
* **Set data in the model.**
  Feed a state variable or parameter received from another component into the model.
  Data is received as :class:`numpy.ndarray`, wrapped in :class:`pint.Quantity`,
  and using one of FINAM's grid types.

Further optional functionality:

* **Get the current simulation time of the model.**
  This can, alternatively, be managed by the wrapper if the model has a fixed time step.
* **Finalize the model.**
  Possibility for cleanup, closing files, etc.

Model wrapper
-------------

The functionality listed above is used by a wrapper for the model the implements the :class:`.TimeComponent` interface.
See chapter :doc:`components` for a walk through of how to write a model wrapper.

The functionality listed above is typically used in the following places:

* Create a model instance, initialize it:

  * in :meth:`.TimeComponent._initialize` if the model setup does not depend on external inputs.
  * in :meth:`.TimeComponent._connect` if the model setup (e.g. the model domain) depends on external inputs.

* Step/update the model:

  * in :meth:`.TimeComponent._update`.

* Finalize the model:

  * in :meth:`.TimeComponent._finalize`.

* Get data, set data:

  * in :meth:`.TimeComponent._update`.
  * in :meth:`.TimeComponent._connect` to push initial data, and to initialize from external inputs.

Local / non-spatial models
--------------------------

Local / non-spatial models can be used in FINAM for spatial simulations by creating and managing
multiple model instances in the :class:`.TimeComponent` wrapper.
E.g. one model instance per grid cell.
This, however, requires that there are no global variables in the model.
I.e. each model instance must be a fully independent object.
