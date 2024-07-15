Persistence in the ODA
==============================

The service uses an implementation of the OSO Data Archive (ODA) for persistence.

The OSO Data Archive (ODA) contains ``Repository`` and ``UnitOfWork`` interfaces which abstract over
database access. There are different implementations of these interfaces, namely ``memory``, ``filesystem``, ``postgres`` and ``rest``.
For more details, see the `ska-db-oda <https://developer.skao.int/projects/ska-db-oda/en/latest/index.html>`_ project.

The important thing for the PTT Services is that it uses ``postgres`` for implementation which will be connecting directly to the PostgreSQL instance.

.. code-block:: yaml

    class Config:
      """
      Config holds the Flask configuration for the ODA REST service.
      """

      ODA_BACKEND_TYPE = "postgres"


This class is defining a configuration setting for the ODA REST service, specifically 
indicating that the backend database type is PostgreSQL.

Here, value of ``ODA_BACKEND_TYPE`` sets to the ``postgres``. 
This attribute likely specifies the type of backend database used by the ODA REST service.
