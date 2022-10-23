=========================
The Connect Phase &trade;
=========================

The "Connect Phase" between linking components and running the composition is a crucial foundation for the coupling principle of FINAM.

During this phase, coupled components exchange metadata about the data to be passed, and the initial data.
FINAM uses an iterative process in order to allow for dependencies between components already before the actual simulation.
This enables components to be initialized based on data received from other components,
without an explicit order. Even circular!

For convenience, `Component` provides the methods `create_connector()` and `try_connect()` for handling this phase.
See section [Implementing The Connect Phase &trade;](implementing-the-connect-phase).

## Metadata

Before data can be passed from an output to an inpout, metadata must be exchanged in both directions.
This has multiple purposes:
* It allows for checking compatibility of connection endpoints
* Adapters can determine the conversions they should perform, e.g. the source and target grid specification and CRS for a regridding adapter
* Components can use metadata from other components for their own initialization (and later calculations)

Using metadata for initialization works in both directions.

A receiving component can use metadata from a linked sending component.
E.g. a component could be initialized from data (and metadata) read by a geodata reader component,
and set up a simulation accordingly.

Contrary, a generating component (e.g. for synthetic landscapes or climate) can use metadata from a linked receiving component.
It can then generate data matching the expected metadata.

Metadata must be provided for all inputs and all outputs.
This can happen in `_initialize()` when constructing inputs and outputs.
If the information is not available there yet (because it depends on linked components),
it can happen in `_connect()` via `try_connect()` (see section [Implementing The Connect Phase &trade;](implementing-the-connect-phase)).

For details on the metadata itself, see chapter [Data and metadata](./data_metadata).

## Data

After metadata was exchanged along a link in both directions, data can be passed.
Components must provide initial data for all outputs.
Further, components can pull data from inputs during The Connect Phase &trade;.

## Iterative connect

The flexibility described above is achieved by an iterative connection process.
The `_connect()` methods of components are called repeatedly.
Components indicate their connect progress via their state:

* `CONNECTED` if everything was exchanged successfully, and initialization in complete
* `CONNECTING` if not completed yet, but some new data or metadata was exchanged that was not in the previous calls
* `CONNECTING_IDLE` if nothing was exchanged that was not already in a previous call

The status is managed internally by the component's `try_connect()` method.
It can, however, be used to check in `_connect()` if The Connect Phase &trade; was completed.

## Circular dependencies

The scheduler tries to repeatedly connect components that not in the `CONNECTED` state yet.
With circular dependencies, this would result in an infinite loop.

To avoid this, there are the two different states `CONNECTING` and `CONNECTING_IDLE`.
If, during an iteration, no component signals any progress (`CONNECTING`, or newly `CONNECTED`), initialization has stalled.
The scheduler raises an error and informs about components that could not complete the process.

(implementing-the-connect-phase)=
## Implementing The Connect Phase &trade;

The iterative connection process is largely managed by two methods provided by `Component`:

### Method `create_connector()`

This method must be called at the end of `_initialize()`, after all inputs and outputs were created.

If the component has no dependencies in this phase, if can be simply called without arguments.

For components with dependencies, they can be specified like this:

```python
self.create_connector(
    required_in_data=["Input_A", "Input_B"],
    required_out_infos=["Output_B", "Output_B"]
)
```

Where strings are the names of inputs and outputs that data or metadata exchange is required for.

* `required_in_data`: inputs that need to be pulled.
* `required_out_infos`: outputs that have incomplete metadata that needs to be filled from connected inputs.

For more on filling incomplete metadata, see section [Metadata from source or target](metadata-from-source-or-target).

### Method `try_connect()`

This method must be called in `_connect()`.
It tried to exchange metadata and data, and sets the component's status to one of
`CONNECTED`, `CONNECTING` or `CONNECTING_IDLE`, depending on the progress.

The method has three optional arguments:

* `exchange_infos`: a dictionary of (newly) available metadata for inputs
* `push_infos`: a dictionary of (newly) available metadata for outputs
* `push_data`: a dictionary of (newly) available data for outputs

Note that `exchange_infos` and `push_infos` are not required for inputs and outputs that were created with metadata in `_initialize()`.

As `_connect()` can be called by the scheduler multiple times,
the above metadata and data can be provided stepwise, as it becomes available.

### The `connector`

The above methods internally call the components `connector` (a `ConnectHelper`).
Besides managing the connection process, it also keeps track of already exchanged metadata and data.
There are several properties that let components access retrieved information,
and check progress:

* `in_infos`: a dictionary of completed/exchanged input metadata infos, may contain `None` values
* `in_data`: a dictionary of successfully pulled input data, may contain `None` values
* `out_infos`: a dictionary of completed/exchanged output metadata, may contain `None` values
* `infos_pushed`: a dictionary of booleans which infos were pushed to outputs
* `data_pushed`: a dictionary of booleans which data was pushed to outputs

### Simple case - no dependencies

In the most simple case, all metadata is known in `_initialze()`, and data is pushed in `_connect()`:

```python
class SimpleConnect(TimeComponent):

    def _initialize(self):
        self.inputs.add(name="A", grid=NoGrid(), units="m")
        self.inputs.add(name="B", grid=NoGrid(), units="m")
        self.outputs.add(name="Area", grid=NoGrid(), units="m2")

        self.create_connector()

    def _connect(self):
        push_data = {"Area": 0}
        self.try_connect(time=self.time, push_data=push_data)
```

In `_initialize()`, we create inputs and outputs with metadata (here `grid` and `units`).
Then, we create the connector with `self.create_connector()`. No arguments required here, as there are no dependencies.

In `_connect()`, we call `self.try_connect()` with a dictionary of all data to push as argument `push_data`.

### More complex - info from input to output

In this example, we want to get a grid specification from an input.
This grid specification should then be used for the metadata of the output,
and the initial data should be generated from it.

```python
class ComplexConnect(TimeComponent):

    def _initialize(self):
        self.inputs.add(name="A", grid=None, units="m")
        self.inputs.add(name="B", grid=NoGrid(), units="m")
        self.outputs.add(name="Area")

        self.create_connector()

    def _connect(self):
        push_infos = {}
        push_data = {}

        pushed = self.connector.data_pushed["Area"]
        info = self.connector.in_infos["A"]
        if not pushed and info is not None:
            push_infos["Area"] = info
            push_data["Area"] = _generate_data(info)

        self.try_connect(time=self.time,
                         push_infos=push_infos,
                         push_data=push_data)
```

In `_initialize()`, we set the `grid` of input `A` to `None`.
It will be filled from the connected output, and becomes available in
`connector.in_infos` after successful exchange.

For output `Area`, we give no metadata at all, which means that we delay specifying it
until we have the grid specification for input `A`.

In `_connect()`, we check if the data was already pushed.
If not, and if the input info is available, we add the output info to be pushed to `push_infos`,
and the generated data to `push_data` (only for a single output here).
Then, `try_connect()` is called with this info and data.

It could happen that `try_connect()` is called with info and data multiple times,
in case only the info can be pushed in a first step, but not the data.
This will not cause any problems. Developers should, however, be aware of this behaviour.
For efficiency, it might be useful to cache the generated output data to avoid
re-generating the data multiple times.

(metadata-from-source-or-target)=
## Metadata from source or target

In the above example, we have already seen the use of a grid specification retrieved from a connected upstream component.
The process works in both directions.

Any metadata field that is initialized with `None` will be filled with the value from the other end of the connection.
This can happen in the initialization of inputs and outputs:

```python
self.inputs.add(name="A", grid=None, units=None)
self.outputs.add(name="Area", grid=NoGrid(), units=None)
```

Here, `grid` and `units` of the input would be filled from a connected output.
For the output, `units` would be filled from a connected input.

The same mechanism can also be applied in `_connect()`:

```python
info = Info(grid=None, units="m")
self.try_connect(time=self.time, in_infos={"A": info})
```

## Summary metadata initialization

To summarize the use of metadata in the initialization of inputs and outputs:

* Set metadata attributes (like `grid` or `units`) to `None` to get them filled from the other end of the connection.
  This will, of course, only work if the respective attributes are given at the other end.
* Set no metadata at all (or use `info=None`) to delay providing it, and do so in `try_connect()`.

## Missing data in adapters

For the iterative initialization, adapters must be able to handle the case of being pulled without data available.

For simple adapters that only overwrite `_get_data()`, developers can rely on the error raised when pulling the adapter's input:

```python
class Scale(Adapter):
    def __init__(self, scale):
        super().__init__()
        self.scale = scale

    def _get_data(self, time):
        # Pull without data available raises FinamNoDataError
        # Simply let it propagate through the adapter chain
        d = self.pull_data(time)
        return d * self.scale
```

Adapters that use push and pull (e.g. for temporal interpolation) must check in `_get_data()` if data is available, and raise a `FinamNoDataError` otherwise:

```python
class PushPullAdapter(Adapter):
    def _source_updated(self, time):
        # Get data here when notified about an upstream update

    def _get_data(self, time):
        ...

        if self.data is None:
            raise FinamNoDataError(f"No data available in {self.name}")

        return self.data
```

## Intercepting metadata in adapters

Usually, adapters simply forward metadata during connecting.
Some adapters, however, change the metadata through their transformation, e.g. the grid specification in a regridding adapter.

Handling and altering incoming and outgoing metadata can be done by overwriting an adapter's `_get_info()` method.
The method is called by an upstream input with the requested metadata, and should return the metadata that will actually be delivered.

The default implementation looks like this:

```
def _get_info(self, info):
    in_info = self.exchange_info(info)
    return in_info
```

The `info` argument is the metadata requested from downstream.
`self.exchange_info(info)` is called to propagate the metadata further upstream.
It returns the metadata received from upstream, and it is simply returned by `_get_info()`.

For a unit conversion adapter, the method could look like this:

```python
def _get_info(self, info):
    in_info = self.exchange_info(info)

    self.out_units = info.units
    out_info = in_info.copy_with(units=self.out_units)

    return out_info
```

> Note that a unit conversion adapter is actually not required, as units are handled by inputs internally.

The adapter gets it's own target units from the `info` coming from downstream, i.e. from the request.
It overwrites the units in the info received from upstream by `in_info.copy_with()`,
and passes the result downstream by returning it.

Note that the method can be called multiple times, as an output or adapter can be connected to multiple inputs.
The adapter is responsible for checking that the metadata of all connected inputs is compatible.
