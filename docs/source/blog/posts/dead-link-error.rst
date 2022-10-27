.. post:: 27 Oct, 2022
    :tags: cookbook, usage
    :category: How to
    :author: Martin Lange
    :excerpt: 2

=============================
Dead link error - what to do?
=============================

When setting up a FINAM composition, you may encounter the scheduler complaining ``Dead link detected between...``.
This post explains what this means, and how to fix it.

Cause of the error
------------------

The error means that you linked the output of a pull-based component (i.e. without time step) to something that needs push.
This can be:

#. A push-based component (i.e. without time step), via adapters or not
#. A time-interpolating adapter

The error message will also show where the problem is.

In problem case 1:

.. code-block:: text

    Output >/> RegridLinear >/> Input

Here, the problem is a push-based component on the right side.
An example could be :class:`SimplexNoise <.modules.SimplexNoise>` as source, and a push-based plot of file writer as target.

In problem case 2:

.. code-block:: text

    Output >/> LinearTime >> Input

Here, the problem is a time-interpolating adapter along the link.
An example could be :class:`SimplexNoise <.modules.SimplexNoise>` as source,
and a :class:`LinearTime <.adapters.LinearTime>` adapter as shown in the above error message.

Fixing the error
----------------

Push-based target problem
^^^^^^^^^^^^^^^^^^^^^^^^^

The problem here is that both linked components have no time step, and none of them will initiate the exchange of data.

The problem can be solved by putting another component with internal time step (i.e. a sub-class of :class:`.ITimeComponent`)
between the two components. Exactly for this purpose, FINAM provides the :class:`TimeTrigger <.modules.TimeTrigger>` component.

Time-interpolating adapter problem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most probably, this is a misconception of the coupling setup.
As the source component has no internal time step, a time-interpolating adapter should not be required.

In cases where the setup is intentional, the same solution as for the `Push-based target problem`_ applies.
