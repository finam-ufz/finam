"""MPI utilities."""
# pylint: disable=E0401


def is_null(comm):
    """Check if the current process is included in an MPI communicator.

    Parameters
    ----------
    comm
        A communicator

    Returns
    -------
    bool
        True if the current process is included in the communicator

    """
    from mpi4py import MPI

    return comm == MPI.COMM_NULL


def create_communicators(processes):
    """Sets up MPI communicators for multiple components by key (e.g. component name).

    Each generated communicator comprises the number of requested processes per key, and the process on rank 0.

    Parameters
    ----------
    processes : dict
        Dictionary of number of processes per key

    Returns
    -------
    dict
        Dictionary of communicators.

    """

    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    requested = sum(processes.values())

    if requested != size - 1:
        raise Exception(
            f"Number of required processes ({requested}) should be one less than available processes ({size})"
        )

    groups = {}

    offset = 1
    for k, n in processes.items():
        r = range(offset, offset + n)
        color = 0 if rank == 0 or rank in r else MPI.UNDEFINED
        group_comm = comm.Split(color, rank)
        groups[k] = group_comm
        offset += n

    return groups
