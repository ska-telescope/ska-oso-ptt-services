.. _rest_api:

REST API
=========

The PTT REST API's support added for get entities, status, put status for EB, SBD, SBI and Project.
There are also GET and PUT method for a resource identifier to retrieve and update the entities, retrospectively.
There are also GET and PUT method for a resource identifier to retrieve and update the status of entities, retrospectively.

Once deployed, the API should be available at ``<HOST>/ptt/api/<MAJOR_VERSION>/<RESOURCE>`` and the Swagger UI at ``<HOST>/api/<MAJOR_VERSION>/ui``.
The host depends on the environment that the server is deployed to, and may include a k8s namespace - see the README for more details. 

The PTT API endpoints, with the accepted requests and expected responses, are documented below:

.. Will be taken care in NAK-1231 MR
.. .. openapi:: ../../openapi/openapi.json
..    :examples:

