# FINAM Python prototype

A minimal interface specification and exemplary implementation for exploration and testing.

* [Interfaces](./finam/core/interfaces.py)
* [SDK](./finam/core/sdk.py)
* [Models](./finam/models)
* [Other modules](./finam/modules)
* [Adapters](./finam/adapters)

For detailed documentation, see module `core` [sources](finam/core/__init__.py)
and [docs](https://landtech.pages.ufz.de/finam-prototype/finam.core.html).

## Running examples

Run the MPI example from the project root:

Linux

```
export PYTHONPATH="formind"
mpirun -n 4 python finam/formind_mpi_test.py --mpi formind 3
```

Windows

```
set PYTHONPATH=formind
mpiexec -n 4 python finam/formind_mpi_test.py --mpi formind 3
```
