Setup
=====
Install the sharutils package-
sudo apt-get install sharutils

Setup Instructions for Kernel, LXC-Docker, and LXC-Docker Extensions (Needed to run the FULL Integration Test task)
https://docs.google.com/a/points.com/document/d/1nZtcjf64Xx1THPQ7mZ79lrxVoqM81PeoVKQqdktsgqc/edit#heading=h.qd3bfnmbs8mm

Create Virtual Environment
mkvirtualenv list_loading_service

Install Dependencies
pip install -r requirements/development.txt

Run unit tests
fab test_units

Run integration tests
fab test_integration

Check flake8
fab flake8

Running List Loading Service
======================

A local list_loading_service server instance can be spawned using the fab task:

  fab runserver

By default the server is configured with the localhost services profile,
which consists of the console logging. It is possible to force the server
to use a different configuration profile as such:

  fab runserver:services_profile=teamcity

The above task will spawn a local server configured to run against the TeamCity
configuration and logging to a rotated file.


Running Tests
=============

There are three types of tests available to this project. Details and
instructions for running each type are as follows:

  Unit Tests
  ----------
  Traditional unit tests with a coverage report can be executed using:

    fab test_units

  Local Integration Tests
  -----------------------
  Lighter weight integration tests can be executed against the local
  environment. These tests exercise the code base against a locally
  spawned List Loading Service application.

  To run them against the local environment:

    fab test_integration

  It is possible to specify another test environment configuration using the
  test_config parameter. To run against an LCP LXC container:

    fab test_integration:test_config=container.ini

  Or against a TeamCity environment:

    fab test_integration:test_config=teamcity.ini

  See lcpenv/README for instructions on spawning an LCP container and database.

  Note that this task only executes tests tagged with the attribute
  'local_integration'. They are normally extensions of the
  BaseIntegrationTestCase or BaseDatabaseTestCase classes.

  Full Integration Tests
  ----------------------
  End-to-end tests that run high-level integration scenarios against a locally
  spawned LCP environment, which includes Core, Gateway, Security services, a
  complete CouchDB database, and all LCP-related infrastructure running on a
  single LXC Vagrant container.

  To learn more about the capabilities of this LCP package, see lcpenv/README.

  To run this set of tests:

    fab test_full_integration

  If you wish for the LCP container to remain up after the tests complete, for
  troubleshooting purposes.

    fab test_full_integration:keeplcp=1

  The LCP environment container can be administered indepedently of the test
  using the following commands:

    fab start_lcp
    fab stop_lcp
    fab destroy_lcp
