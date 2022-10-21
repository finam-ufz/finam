# Interfaces

FINAM is primarily a collection of interfaces that allows different models and other components to communicate.

For all interfaces, FINAM also provides abstract or concrete implementations to speed up component development.

## Class diagram

The following figure shows a diagram of FINAM's core interfaces and classes.
Arrows indicate inheritance.
The properties and methods are those typically used or implemented by developers.

<img width="100%" src="../images/class-diagram-core.svg" />

## Components

Components represent linkable entities like models.
There are two interfaces for components: `IComponent` and `ITimeComponent`.

### `IComponent`

`IComponent` serves for pull-based components without an explicit time step.
It provides all the basic methods required for component communication and execution.

* `initialize(self)` sets up the component
* `connect(self)` pushes initial values to output slots
* `validate(self)` checks the component for validity
* `update(self)` makes a calculation step
* `finalize(self)` shuts down the component

These methods are called by the scheduler in the given order (and repeatedly for `update()`), each for all components, before proceeding to the next method.

For each of these methods, there is a private method with the same name and an underscore prefix, like `_initialize(self)`.
Component developers implement these private methods, which are called internally by their public counterpart.
For details, see chapter [Writing components](./components).

To access a component's input and output slots, there are the properties:

* `inputs` returns a `dict-like` of `IInput` slots by name
* `outputs` returns a `dict-like` of `IOutput` slots by name

Finally:

* `status` returns the component's current `ComponentStatus` (`CREATED`, `INITIALIZED`, ...)

The abstract class `Component` provides a basic implementation for `IComponent`.
Classes extending `Component` must override methods named of the first block, with underscore, like `_initialize()`.
`inputs`, `outputs` and `status` are provided as basic implementations.

### `ITimeComponent`

`ITimeComponent` extends `IComponent` and serves for components with explicit time step, like simulation models.
In addition to `IComponent`, it adds one property:

* `time` should report the component's current time, as a `datetime` object

As `ITimeComponent` extends `IComponent`, only `ITimeComponent` needs to be implemented.

The abstract class `TimeComponent` provides a basic implementation for `ITimeComponent`.
It is basically identical to `Component`, and in addition provides a basic implementation for `time`.

## Inputs and Outputs

Interfaces `IInput` and `IOutput` define coupling slots.

In module `sdk`, `Input` and `Output` are provided as implementations for `IInput` and `IOutput`, respectively.
They should suffice most use cases.

### `IInput`

`IInput` represents a data exchange input slot, with the following methods:

* `set_source(self, source)` sets an `IOutput` as source for this input
* `get_source(self)` returns the `IOutput` that is the source for this input
* `source_updated(self, time)` informs the input that the connected `IOutput` has new data available
* `pull_data(self, time)` retrieves and returns the connected `IOutput`'s data

Components usually only use `pull_data(self, time)` in their `_update(self)` method.
All other methods are only used under the hood.

All these methods are implemented in `Input`, so there is normally no need to write an own implementation for `IInput`.

Another implementation is provided by `CallbackInput`, for use in push-based components without a time step.
They can connect to `source_updated(self, time)` by providing a callback function.

Other classes derived from `Input` can overwrite the private `_source_updated(self, time)` method,
which is called by `source_updated(self, time)`.

### `IOutput`

`IOutput` represents a data exchange output slot, with the following methods:

* `add_target(self, target)` adds an `IInput` as target for this output
* `get_target(self)` returns the list of `IInput` targets of this output
* `push_data(self, data, time)` is used to populate the output with data after an update
* `notify_targets(self, time)` informs coupled `IInput`s that new data is available
* `get_data(self, time)` returns the data in this output
* `chain(self, input)` connects this output to an `IInput` (or an adapter)

Components usually only use `_push_data(self, data, time)` in their `update(self)` method.
During coupling setups, `chain(self, input)` or it's synonym operator `>>` are used.
All other methods are only used under the hood.

All these methods are implemented in `Output`, so there is normally no need to write an own implementation for `IOutput`.

Other classes derived from `Output` can overwrite the private `_get_data(self, time)` method,
which is called by `get_data(self, time)`.

## Adapters

Adapters serve for data transformations between outputs and inputs of different components.

### `IAdapter`

The interface `IAdapter` serves for implementing adapters.
It simply combines `IInput` and `IOutput`, so it is both at the same time.
`IAdapter` provides all the methods of `IInput` and `IOutput`, but most of them are only used under the hood.

Classes implementing `IAdapter` can extend `Adapter`, which provides default implementations for `Input` and `Output` methods.

Time-independent/one-shot adapters need to override `_get_data(self, time)`.
Inside this method, they get their input via `self.pull_data(time)`, transform it, and return the result.

Time-aware adapters, e.g. for temporal interpolation, usually override `_source_updated(self, time)` and `_get_data(self, time)`.
In `_source_updated(self, time)`, incoming data is collected (and potentially aggregated), while in `_get_data(self, time)` the result is returned.

For details, see chapter [Writing adapters](./adapters).

### `NoBranchAdapter`

Some time-aware adapters may not allow for branching in the subsequent adapter chain.
I.e. they do not support multiple target components.
For these cases, `NoBranchAdapter` is provided as a marker interface without any methods.
