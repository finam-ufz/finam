======================
Logging for components
======================

This chapter provides information on how to use logging in components.

It is assumed that you have read the chapter about :doc:`./components` and the chapter on how to
configure the logger in the :doc:`composition <../usage/coupling_scripts>`.

Using the logger in components
------------------------------

The component base classes :class:`.Component` and :class:`.TimeComponent` are by default loggable, that means,
they have a property called :attr:`logger <.Component.logger>` you can use in every method beside ``__init__``.

That logger provides simple methods to log a certain message:

* :meth:`logger.debug() <logging.Logger.debug>`: write a debug message
* :meth:`logger.info() <logging.Logger.info>`: write an info message
* :meth:`logger.warning() <logging.Logger.warning>`: write a warning

Here is an example using the dummy model from the previous chapter:

.. testcode:: component-logging

    import finam as fm


    class DummyModel(fm.TimeComponent):

        def __init__(self, **config):
            super().__init__()
            # your setup

        def _next_time(self):
            return self.time # + step

        def _initialize(self):
            self.logger.debug("trying to initialize the dummy model")

            self.inputs.add(name="A")
            self.outputs.add(name="B")
            self.create_connector()

            self.logger.info("dummy model initialized")

.. testcode:: component-logging
    :hide:

    comp = DummyModel()
    comp._initialize()

Using this dummy model in a composition would return something similar to this (with ``log_level=logging.DEBUG``):

.. code-block::

    2022-08-26 11:31:28,283 - FINAM.DummyModel - DEBUG - init
    2022-08-26 11:31:28,284 - FINAM.DummyModel - DEBUG - trying to initialize the dummy model
    2022-08-26 11:31:28,285 - FINAM.DummyModel - INFO - dummy model initialized


When using ``log_level=logging.INFO``, all debug message would be ignored.

This is convenient because most developers put print message in their code during development and debugging and
when using the logger instead of plain print statements, you are able to keep these debugging message.

Logging of raised errors
------------------------

Developers may implement checks in the components and want to raise Errors, if something is wrong.
In order to show these errors in the logger, we provide a context manager :class:`.ErrorLogger`:

.. testcode:: error-logging

    import finam as fm
    from finam.tools import ErrorLogger


    class DummyModel(fm.TimeComponent):

        def __init__(self):
            super().__init__()

        def _next_time(self):
            return self.time # + step

        def _initialize(self):
            with ErrorLogger(self.logger):
                raise NotImplementedError("this is not implemented yet")

.. testcode:: error-logging
    :hide:

    comp = DummyModel()
    try:
        comp._initialize()
    except NotImplementedError:
        pass

This will log the error and raise it. Without the context manager, the error would be raised but not logged.

Logging of output of external models
------------------------------------

Since FINAM is made to use external models, we also provide convenience functions to log model output, that would be printed to the terminal.

In order to do so, we provide context managers to redirect ``stdout`` and ``stderr`` to the logger. There are two types:

- :class:`.LogStdOutStdErr`: Context manager to redirect stdout and stderr to a logger.
- :class:`.LogCStdOutStdErr`: Context manager to redirect low-level C stdout and stderr to a logger.

When using a compiled extension from Fortran or C, you should use :class:`.LogCStdOutStdErr`, because they use a different framework for printing to stdout/stderr.

Here is an example on how to use these:

.. code-block:: Python

    import finam as fm
    from finam.tools import LogCStdOutStdErr
    from yourmodel import model


    class DummyModel(fm.TimeComponent):

        def __init__(self):
            super().__init__()
            self.model = model()

        def _initialize(self):
            with LogCStdOutStdErr(self.logger):
                self.model.init()

This will redirect all outputs of ``model.init()`` to the logger of the component as ``INFO`` (stdout) and ``WARN`` (stderr) messages.

You can also configure each log-level with:

.. code-block:: Python

    LogCStdOutStdErr(self.logger, level_stdout=logging.INFO, level_stderr=logging.WARN)

The :class:`.LogStdOutStdErr` context manager works the exact same way but for Pythons stdout and stderr.
