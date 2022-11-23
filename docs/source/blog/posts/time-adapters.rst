.. post:: 23 Nov, 2022
    :tags: announcement, cookbook, usage, v0.4
    :category: How to
    :author: Martin Lange
    :excerpt: 1
    :image: 1

==================================
Time interpolation and integration
==================================

With version ``v0.4.0``, FINAM comes with a set of **new time interpolation and integration adapters**.
In addition to the existing linear interpolation adapter,
**step-wise interpolation** with a flexible step position is now available.
Integration over the target component's time step supports averaging as well as **sum integration** (Area under Curve).

----

In many FINAM coupling use cases, components will have different time steps.
This requires ways to deal with data pulls that lie between push times,
and with target time steps covering multiple source steps.

FINAM provides several adapters for time interpolation and integration
to provide the right method for a wide range of use cases.

Time interpolation
------------------

Time interpolation is most useful for models with time steps of the same order of magnitude,
or if the target time step is smaller than the source time step.

Time interpolation adapters interpolate between the two adjacent data entries.
In the illustration below, data entries are denoted by black circles.
Interpolation results for linear and step-wise interpolation are shown as colored lines.

.. plot:: api/plots/interpolation-methods.py

    Illustration of interpolation methods.

FINAM provides these time interpolation adapters:

* :class:`.adapters.LinearTime` -- Linear time interpolation.
* :class:`.adapters.StepTime` -- Step-wise time interpolation with adjustable step position.

Time integration
----------------

Time integration is particularly useful in cases where the target has a much longer time step than the source.
In these cases, interpolation would just provide a snapshot of the current data,
but ignore the history over the longer time step.

Further, sum integration (Area under Curve) allows to aggregate rate-like data (e.g. precipitation in *mm/d*)
to amounts (e.g. total precipitation over the time step, in *mm*).

Time integration adapters in FINAM keep track of pull events from the target,
and aggregate data between the last and the current pull.
This is illustrated in the figure below.

.. plot:: api/plots/integration-methods.py

    Illustration of time integration.

.. note::
    Time integration also requires an interpolation method.
    The illustration uses linear interpolation, but step-wise interpolation is also supported
    by all integration adapters.

FINAM provides these time integration adapters:

* :class:`.adapters.AvgOverTime` -- Time-weighted average integration.
* :class:`.adapters.SumOverTime` -- Sum/Area under Curve integration.

.. note::
    The :class:`SumOverTime <.adapters.SumOverTime>` adapter may change units, depending on the setup.
    This also allows to transform rates into amounts, like *mm/d* to total *mm*.
