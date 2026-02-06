.. post:: 05 Feb, 2026
    :tags: cookbook, usage, v1.0
    :category: How to
    :author: Thomas Fischer
    :excerpt: 1

==========================================================================
What needs to be done for coupling with FINAM - the model code perspective
==========================================================================

Lets start clarifying what is meant by coupling. Wikipedia describes coupling
as follows: "A coupling is a device used to connect two shafts together at
their ends for the purpose of transmitting power." By analogy, `FINAM`_ is the
device and a modeling software corresponds to a component. The purpose of
the coupling is transmitting data from one component to another. Here, the
coupling isn't limited to two components. It may very well be possible that
several models can be sensibly coupled.

.. _FINAM: https://finam.pages.ufz.de/

But just like in the physical world, the components must also fit together in
the software world. This is also known as the interface. In the analog world
glue is used to connect the two parts - in our case we use the Python
programming language as glue.

To make it possible to couple a modeling software to FINAM it is neccessary to
implement the corresponding interface. The `FINAM component interface`_ consists
only of a few functions that needs to be provided by the model.

.. _FINAM component interface: https://finam.pages.ufz.de/finam/api/generated/finam.TimeComponent.html#finam.TimeComponent

If the model is designed with coupling in mind, the
implementation of the interface shouldn't be a big deal. For models that were
not developed with the aim of coupling, however, it may be necessary and
challenging to refactor at least parts of the existing code in order to
implement the interface.

Lets look at `OpenGeoSys`_. It is a software that is able to solve coupled
thermo-hydro-mechanical processes in fractured porous media. It has been under
developement for more than 3 decades. In the past, OpenGeoSys was used as a
stand-alone application (monolithic execution) and it wasn't the aim to couple
other simulation software with OpenGeoSys. Now, with the coupling of different
simulation softwares new opportunities open up to investigate the interaction
of different compartments.

.. _OpenGeoSys: https://www.opengeosys.org/

In order to change the design of OpenGeoSys it was necessary to understand the
general phases of a simulation run. Up to now, an OpenGeoSys simulation has run
in several closely interlinked phases. The first phase
involved reading in the configuration file and the input grids. In the next
phase, the temporal development of the simulated process is calculated in a
so-called time loop. In the first iteration of this time loop, all of OGS's own
internal data structures were initialized. After the last time iteration the
data structures have to be cleaned up.

As a result of the new requirements the more or less monolithic time loop code
executed in the main function was decomposed to several separate functions.
At the beginning of the refactorizations the time loop code consisted of several
hundreds of lines. Some of the functionalities are
moved to the newly created class Simulation. This class offers a small
interface with functions for different phases of the simulation like for
initialization of data structures, executing a time step, or input and output of
data to OGS. Exactly this functionality is required by a coupling framework and
is wrapped using `pybind11`_. These OGS Python bindings can be directly used in the
`FINAM-OGS6`_ component.

.. _pybind11: https://pybind11.readthedocs.io/en/stable/index.html
.. _FINAM-OGS6: https://git.ufz.de/FINAM/finam-ogs6

In addition, after each time loop
iteration, control should be returned to FINAM so that other models can perform
their calculations with the intermediate OGS results. Therefore it was necessary
to implement an external access to the intermediate OGS data. But accessing
the data alone was not enough to do the job. For instance, for the data exchange
between OGS and FINAM the same mesh data layouts are required. Therefore the
data layout had to be adjusted in the FINAM-OGS6 Python wrapper.

Many other things have changed under the hood like the pre and post time step
calculations are extracted to own functions, the encapsulation of the
calculation of the size of the next time step in the TimeStepAlgorithm class
hierarchy was improved, or the deentanglement of the time management and
consistent storage of the time.

Positive effects of the code changes (often called refactorization) were better
modularity, encapsulation, an improved readability, and enhanced maintainability.
Furthermore, these changes made it possible to write unit tests for the
extracted functionality. The new unit tests will facilitate future code changes.

Now, OpenGeoSys can be easily connected with other modeling softwares or IO
components!
