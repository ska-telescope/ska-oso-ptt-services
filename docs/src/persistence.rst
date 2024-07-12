Persistence in the ODA
==============================

The service uses an implementation of the OSO Data Archive (ODA) for persistence.

The OSO Data Archive (ODA) contains ``Repository`` and ``UnitOfWork`` interfaces which abstract over
database access. There are different implementations of these interfaces, namely ``memory``, ``filesystem``, ``postgres`` and ``rest``.
For more details, see the `ska-db-oda <https://developer.skao.int/projects/ska-db-oda/en/latest/index.html>`_ project.

The important thing for the PTT Services is that the implementation can be configured at deploy time, by setting an environment variable through the Helm value:

.. code-block:: yaml

    rest:
      ...
      oda:
        backendType: postgres
        url:
      ...



The OSO PTT Services uses ``postgres`` for database implementation which will be be connecting directly to the PostgreSQL instance.
