"""
Coupling framework core. Interfaces and their basic (abstract) implementations.

Interfaces
==========

An example coupling setup with elements labelled by the required interfaces:

.. code-block:: text

                                                                       +------------------+
                                                 .------------> IInput | IComponent       |
                                                /                      +------------------+
    +-------------------+                      /                       +------------------+
    |                   | IOutput --> IAdapter --> IAdapter --> IInput |                  |
    |  IComponent       |                                              |  IComponent      |
    |    or             | IInput <--------- IAdapter <-------- IOutput |    or            |
    |  ITimeComponent   |                                              |  ITimeComponent  |
    |                   | IInput <-- IAdapter <-- IAdapter <-- IOutput |                  |
    +-------------------+                                              +------------------+

    ---> = data flow

Modules and Models
==================

Modules without a time step need to implement :class:`.interfaces.IComponent`.
An abstract implementation to start module development is provided by :class:`.sdk.AComponent`.
Modules without time steps are updated by a push-based strategy when new data becomes available to input slots.

Simulation models and other modules with explicit time steps need to implement :class:`.interfaces.ITimeComponent`.
The abstract implementation to start development is provided by :class:`.sdk.ATimeComponent`.
Modules with explicit time steps are updated by the framework's driver.

Inputs and Outputs
==================

Input and output interfaces are defined in :class:`.interfaces.IInput` and :class:`.interfaces.IOutput`.

Default implementations for input and output slots are provided by :class:`.sdk.Input` and :class:`.sdk.Output`.
For modules without time steps, :class:`.sdk.CallbackInput` provides an implementation where the module can
receive notifications when new data becomes available.

Adapters
========

Data can be mediated between coupled outputs and inputs through adapters.
An incomplete list of possible transformations are:

* Unit conversion
* Conversion between data types (e.g. raster to polygon)
* Reprojection of geographic data
* Spatial aggregation
* Temporal interpolation, aggregation and integration
* ...

Adapters must implement :class:`.interfaces.IAdapter`,
which inherits :class:`.interfaces.IInput` and :class:`.interfaces.IOutput`.
An abstract implementation is provided by :class:`.sdk.AAdapter`.

Information Flow
================

This prototype is based on a **hybrid push-pull information flow**. Modules "push" data updates to their outputs.
These default outputs (:class:`.sdk.Output`) store the data,
and notify all connected inputs and adapters (targets) that new data is available, but without passing the data itself.
Adapters forward these notifications, until the input of another module is reached.

Modules with time steps are **updated by the driver**, while modules without time steps **update when notified**
about new data. They are then free to pull data from their inputs.
In the most basic case, this pull propagates backwards through the chain of adapters until a module's output is reached,
where the latest available data was stored during the push. Adapters handle the data sequentially, and the pulled input
returns the transformed data for usage in the model or module.

The scheduling of the driver ensures that the requested data is always available.

There is one category of adapters that requires a different strategy:
those intended for **temporal interpolation, aggregation, etc**.
Such time-dependent adapters need to transform data from multiple points in time
to data for one particular requested point in time.
For that sake, these adapters do not simply execute their operations during pull.
When notified about new input data that became available, the adapter pulls that data and store it internally.
When data is pulled from downstream the adapter, it does its calculations
(e.g. temporal interpolation for the requested point in time) and returns the result.

Time-related adapters should still forward notifications, just as usual adapters do.
"""

from . import interfaces, sdk, schedule, mpi
