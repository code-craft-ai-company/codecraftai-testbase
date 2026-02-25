.. _06-00-distributed-test-execution:

***************************
Distributed Test Execution
***************************

Audience
--------

QA engineers and developers implementing distributed test execution with ``automojo.testbase``.


Overview
--------

The Result Concentrators system provides infrastructure for aggregating test execution progress and results from distributed test execution environments. It enables:

- Real-time progress collection from remote test workers via HTTP callbacks
- Centralized progress tracking and status aggregation
- Periodic forwarding of aggregated summaries to external monitoring services
- Thread-safe concurrent progress updates from multiple sources

The system operates as a service layer that sits between distributed test workers and the central ``ResultRecorder``, providing a unified view of test execution progress across multiple processes or machines.


Architecture
------------

The distributed test execution architecture consists of three main components:

1. **ProgressConcentratorServer** - A threaded HTTP server that receives progress callbacks from remote test workers
2. **ProgressCallbackHandler** - An HTTP request handler that processes incoming POST requests containing progress information
3. **ResultRecorder** - The central component that maintains running task state and provides thread-safe summary access

.. code-block:: text

    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │   Worker 1      │     │   Worker 2      │     │   Worker N      │
    │  (Remote Host)  │     │  (Remote Host)  │     │  (Remote Host)  │
    └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
             │                       │                       │
             │  HTTP POST /progress  │                       │
             └───────────────────────┼───────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │  ProgressConcentratorServer    │
                    │  (Central Aggregation Point)   │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │       ResultRecorder           │
                    │  (Progress State & Summary)    │
                    └────────────────────────────────┘


Setting Up the Concentrator Server
----------------------------------

Basic Server Setup
~~~~~~~~~~~~~~~~~~

To create and start a concentrator server, you need a ``ResultRecorder`` instance and a server address:

.. code-block:: python

    from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder
    from automojo.testbase.results.concentrators.progressconcentratorservice import (
        ProgressConcentratorServer
    )

    # Create the recorder (see Result Recording documentation for details)
    recorder = create_your_recorder()

    # Create the concentrator server
    server_address = ("127.0.0.1", 8080)  # Listen on localhost:8080

    server = ProgressConcentratorServer(
        recorder=recorder,
        server_address=server_address,
        forwarding_info=None,  # No forwarding
        bind_and_activate=True
    )

    # Start the server
    server.start()

    print(f"Server ready at http://{server_address[0]}:{server_address[1]}/")


Server Address Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``server_address`` parameter is a tuple of ``(host, port)``:

- Use ``"127.0.0.1"`` to listen only on the loopback interface (local connections only)
- Use ``"0.0.0.0"`` to listen on all available network interfaces (allows remote connections)

.. code-block:: python

    # Local-only server (for single-machine distributed testing)
    local_server = ProgressConcentratorServer(
        recorder=recorder,
        server_address=("127.0.0.1", 8080),
        forwarding_info=None,
        bind_and_activate=True
    )

    # Network-accessible server (for multi-machine distributed testing)
    network_server = ProgressConcentratorServer(
        recorder=recorder,
        server_address=("0.0.0.0", 9090),
        forwarding_info=None,
        bind_and_activate=True
    )


Thread Management
~~~~~~~~~~~~~~~~~

The concentrator server manages two types of threads:

1. **Server Thread** - Named ``prog-concentrator``, handles incoming HTTP requests
2. **Forwarding Thread** - Named ``prog-forwarder``, periodically forwards summaries (when configured)

Both threads are created as daemon threads, which means they will automatically terminate when the main process exits. The ``start()`` method uses gate synchronization to ensure the server is fully ready before returning.


Submitting Progress from Workers
--------------------------------

Remote workers submit progress updates via HTTP POST requests with JSON payloads.


Creating Progress Updates
~~~~~~~~~~~~~~~~~~~~~~~~~

Workers create ``ProgressInfo`` objects to represent their current state:

.. code-block:: python

    from datetime import datetime
    import uuid

    from automojo.testbase.results.model.progresscode import ProgressCode
    from automojo.testbase.results.model.progressinfo import ProgressInfo
    from automojo.testbase.results.model.progresstype import ProgressType

    # Create a progress update
    progress = ProgressInfo(
        id=str(uuid.uuid4()),           # Unique task identifier
        category="test-execution",       # Category of the task
        moniker="test_module.test_func", # Human-readable task name
        ptype=ProgressType.Sequential,   # Progress tracking mode
        range_min="0",                   # Minimum progress value
        range_max="10",                  # Maximum progress value
        position="5",                    # Current progress position
        status=ProgressCode.Running,     # Current status
        when=datetime.now(),             # Timestamp of the update
        data={                           # Optional additional data
            "worker_id": "worker-1",
            "additional_info": "Processing step 5 of 10"
        }
    )


Submitting Progress via HTTP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Workers submit progress updates using HTTP POST with JSON:

.. code-block:: python

    import requests

    # Convert progress to dictionary for JSON serialization
    payload = progress.as_dict()

    # Submit to the concentrator server
    url = "http://concentrator-host:8080/"
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Progress update submitted successfully")
    else:
        print(f"Error: {response.status_code}")


Progress Status Codes
~~~~~~~~~~~~~~~~~~~~~

The ``ProgressCode`` enumeration defines the available task states:

+---------------+--------------------------------------------------+
| Status        | Description                                      |
+===============+==================================================+
| ``NotStarted``| Task is queued but not yet running               |
| ``Running``   | Task is actively executing                       |
| ``Paused``    | Task execution is temporarily suspended          |
| ``Completed`` | Task finished successfully (removed from tracker)|
| ``Failed``    | Task failed due to assertion failure             |
| ``Errored``   | Task failed due to unexpected exception          |
+---------------+--------------------------------------------------+

When a task reports ``Completed`` status, it is automatically removed from the ``running_tasks`` dictionary in the recorder.


Progress Types
~~~~~~~~~~~~~~

The ``ProgressType`` enumeration defines how progress is tracked:

+------------------+--------------------------------------------------+
| Type             | Use Case                                         |
+==================+==================================================+
| ``Sequential``   | Multi-step operations (step 3 of 5)              |
| ``NumericRange`` | Batch processing with known count (450 of 1000)  |
| ``TimeSpan``     | Duration-based tasks (1800s of 3600s elapsed)    |
+------------------+--------------------------------------------------+


Progress JSON Payload Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The JSON payload sent to the concentrator server has the following structure:

.. code-block:: json

    {
        "id": "task-uuid-123",
        "category": "test-execution",
        "moniker": "test_module.test_function",
        "ptype": "Sequential",
        "range_min": "0",
        "range_max": "10",
        "position": "5",
        "status": "Running",
        "when": "2025-02-20T10:30:00.000000",
        "data": {
            "worker_id": "worker-1",
            "additional_info": "..."
        }
    }


Complete Worker Example
~~~~~~~~~~~~~~~~~~~~~~~

Here is a complete example of a worker submitting progress updates:

.. code-block:: python

    import requests
    import uuid
    from datetime import datetime

    from automojo.testbase.results.model.progresscode import ProgressCode
    from automojo.testbase.results.model.progressinfo import ProgressInfo
    from automojo.testbase.results.model.progresstype import ProgressType


    def run_worker_task(concentrator_url: str, worker_id: str):
        """
            Execute a task and report progress to the concentrator.
        """
        task_id = str(uuid.uuid4())
        headers = {"Content-Type": "application/json"}

        # Report task started
        progress = ProgressInfo(
            id=task_id,
            category="test-execution",
            moniker=f"worker_{worker_id}.my_task",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="5",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            data={"worker_id": worker_id}
        )
        requests.post(concentrator_url, json=progress.as_dict(), headers=headers)

        # Execute task steps
        for step in range(1, 6):
            # ... do work ...

            # Report progress
            progress.position = str(step)
            progress.when = datetime.now()
            requests.post(concentrator_url, json=progress.as_dict(), headers=headers)

        # Report task completed
        progress.status = ProgressCode.Completed
        progress.when = datetime.now()
        requests.post(concentrator_url, json=progress.as_dict(), headers=headers)



Progress Forwarding Configuration
---------------------------------

The concentrator server can periodically forward aggregated summaries to external monitoring services. This enables real-time dashboards and integration with external monitoring systems.


ForwardingInfo Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure forwarding using the ``ForwardingInfo`` dataclass:

.. code-block:: python

    from automojo.testbase.results.model.forwardinginfo import ForwardingInfo

    forwarding_info = ForwardingInfo(
        forwarding_interval=5.0,  # Forward every 5 seconds
        forwarding_url="https://monitoring.example.com/api/progress",
        forwarding_headers={
            "Authorization": "Bearer your-api-token",
            "X-Job-Id": "job-456"
        }
    )

ForwardingInfo Fields
~~~~~~~~~~~~~~~~~~~~~

+------------------------+----------+--------------------------------------------------+
| Field                  | Type     | Description                                      |
+========================+==========+==================================================+
| ``forwarding_interval``| ``float``| Seconds between summary forwards                 |
| ``forwarding_url``     | ``str``  | Destination URL for POST requests                |
| ``forwarding_headers`` | ``dict`` | Optional custom HTTP headers (merged with        |
|                        |          | default ``Content-Type: application/json``)      |
+------------------------+----------+--------------------------------------------------+


Starting Server with Forwarding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass the ``ForwardingInfo`` to the server constructor:

.. code-block:: python

    from automojo.testbase.results.model.forwardinginfo import ForwardingInfo
    from automojo.testbase.results.concentrators.progressconcentratorservice import (
        ProgressConcentratorServer
    )

    # Configure forwarding
    forwarding_info = ForwardingInfo(
        forwarding_interval=5.0,
        forwarding_url="https://monitoring.example.com/api/progress",
        forwarding_headers={
            "Authorization": "Bearer token123",
            "X-Job-Id": "job-456"
        }
    )

    # Create server with forwarding enabled
    server = ProgressConcentratorServer(
        recorder=recorder,
        server_address=("0.0.0.0", 8080),
        forwarding_info=forwarding_info,
        bind_and_activate=True
    )

    # Start the server (this also starts the forwarding thread)
    server.start()


Forwarding Interval Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose the forwarding interval based on your monitoring requirements:

+------------------+--------------------------------------------------+
| Interval         | Use Case                                         |
+==================+==================================================+
| 1-2 seconds      | Real-time dashboards requiring immediate updates |
| 5-10 seconds     | Standard monitoring with reasonable responsiveness|
| 30+ seconds      | Low-priority monitoring, reduced network traffic |
+------------------+--------------------------------------------------+

.. note::

    High-frequency forwarding increases network traffic. Consider the trade-off between responsiveness and resource usage.


Authentication Headers
~~~~~~~~~~~~~~~~~~~~~~

For secure monitoring endpoints, include authentication headers:

.. code-block:: python

    # Bearer token authentication
    forwarding_info = ForwardingInfo(
        forwarding_interval=10.0,
        forwarding_url="https://secure-monitoring.example.com/api/progress",
        forwarding_headers={
            "Authorization": "Bearer your-api-token-here",
            "X-Correlation-Id": str(uuid.uuid4())
        }
    )

    # API key authentication
    forwarding_info = ForwardingInfo(
        forwarding_interval=10.0,
        forwarding_url="https://api.example.com/progress",
        forwarding_headers={
            "X-API-Key": "your-api-key-here"
        }
    )


Environment-Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure different forwarding settings for different environments:

.. code-block:: python

    import os

    environment = os.environ.get("ENVIRONMENT", "development")

    if environment == "production":
        forwarding_info = ForwardingInfo(
            forwarding_interval=30.0,  # Less frequent in production
            forwarding_url="https://monitoring.prod.example.com/api/progress",
            forwarding_headers={
                "Authorization": f"Bearer {os.environ['PROD_API_TOKEN']}",
                "X-Environment": "production"
            }
        )
    else:
        forwarding_info = ForwardingInfo(
            forwarding_interval=2.0,  # More frequent in development
            forwarding_url="http://localhost:3000/api/progress",
            forwarding_headers={
                "X-Environment": "development"
            }
        )


Forwarding Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

The forwarding thread handles errors gracefully:

- Network errors are caught and logged
- The forwarding loop continues after errors
- The server remains operational even if forwarding fails

Errors are logged using the ``EnhancedLogger`` and include the full exception traceback.


Monitoring Integration
----------------------

The concentrator server integrates with external monitoring services through the summary forwarding mechanism.


Summary JSON Structure
~~~~~~~~~~~~~~~~~~~~~~

The forwarded summary has the following structure:

.. code-block:: json

    {
        "version": "2",
        "title": "Test Run Title",
        "runid": "uuid-string",
        "build": {
            "release": "1.0.0",
            "branch": "main",
            "build": "123",
            "flavor": "release",
            "url": "https://..."
        },
        "pipeline": {
            "id": "pipeline-id",
            "name": "pipeline-name",
            "instance": "instance-id"
        },
        "job": {
            "id": "job-id",
            "initiator": "user",
            "label": "job-label",
            "name": "job-name",
            "owner": "owner",
            "type": "test",
            "venue": "local",
            "seed": "seed-value",
            "tag": "tag-value"
        },
        "start": "2025-02-20T10:00:00",
        "stop": null,
        "result": "RUNNING",
        "apod": "automation-pod-name",
        "totals": null,
        "running": {
            "task-id-1": { ... },
            "task-id-2": { ... }
        }
    }


Integrating with Dashboards
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To integrate with a monitoring dashboard:

1. **Create an endpoint** on your monitoring service that accepts POST requests with JSON payloads
2. **Configure forwarding** to point to your endpoint
3. **Parse the summary** to extract relevant metrics

Example dashboard endpoint (Flask):

.. code-block:: python

    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route('/api/progress', methods=['POST'])
    def receive_progress():
        summary = request.get_json()

        # Extract metrics
        result = summary.get('result', 'UNKNOWN')
        running_tasks = len(summary.get('running', {}))
        start_time = summary.get('start')

        # Store or display metrics
        update_dashboard(result, running_tasks, start_time)

        return jsonify({"status": "received"}), 200


Integrating with Prometheus
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To expose metrics for Prometheus scraping, create a metrics endpoint:

.. code-block:: python

    from prometheus_client import Counter, Gauge, generate_latest

    # Define metrics
    running_tasks_gauge = Gauge('testbase_running_tasks', 'Number of running tasks')
    completed_tasks_counter = Counter('testbase_completed_tasks', 'Total completed tasks')

    @app.route('/api/progress', methods=['POST'])
    def receive_progress():
        summary = request.get_json()

        # Update Prometheus metrics
        running_tasks_gauge.set(len(summary.get('running', {})))

        return jsonify({"status": "received"}), 200

    @app.route('/metrics')
    def metrics():
        return generate_latest()


Integrating with Grafana
~~~~~~~~~~~~~~~~~~~~~~~~

For Grafana integration:

1. Set up a data source (Prometheus, InfluxDB, or JSON API)
2. Configure forwarding to send summaries to your data source
3. Create dashboards to visualize test execution progress

Example InfluxDB integration:

.. code-block:: python

    from influxdb_client import InfluxDBClient, Point

    @app.route('/api/progress', methods=['POST'])
    def receive_progress():
        summary = request.get_json()

        # Write to InfluxDB
        point = Point("test_execution") \
            .tag("job_id", summary.get('job', {}).get('id', 'unknown')) \
            .field("running_tasks", len(summary.get('running', {}))) \
            .field("result", summary.get('result', 'UNKNOWN'))

        write_api.write(bucket="testbase", record=point)

        return jsonify({"status": "received"}), 200


Webhook Integration
~~~~~~~~~~~~~~~~~~~

For webhook-based integrations (Slack, Teams, etc.):

.. code-block:: python

    import requests

    @app.route('/api/progress', methods=['POST'])
    def receive_progress():
        summary = request.get_json()

        # Check for completion or failure
        result = summary.get('result')
        if result in ['PASSED', 'FAILED', 'ERRORED']:
            # Send webhook notification
            webhook_url = "https://hooks.slack.com/services/..."
            message = {
                "text": f"Test run completed: {result}",
                "attachments": [{
                    "color": "good" if result == "PASSED" else "danger",
                    "fields": [
                        {"title": "Job", "value": summary.get('job', {}).get('name')},
                        {"title": "Result", "value": result}
                    ]
                }]
            }
            requests.post(webhook_url, json=message)

        return jsonify({"status": "received"}), 200


Concurrent Request Handling
---------------------------

The concentrator server uses ``ThreadingMixIn`` to handle multiple simultaneous requests from workers.


Thread Safety
~~~~~~~~~~~~~

- Each incoming request is handled in a separate thread
- The ``ResultRecorder.post_task_progress()`` method is thread-safe
- The ``ResultRecorder.summary`` property returns a thread-safe copy

This allows multiple workers to submit progress updates simultaneously without data corruption.


Scaling Considerations
~~~~~~~~~~~~~~~~~~~~~~

For large-scale distributed testing:

- The server can handle many concurrent connections
- Lock contention is minimized through short critical sections
- Summary copies prevent lock holding during forwarding

.. note::

    For very high-scale deployments, consider running multiple concentrator instances behind a load balancer.


Error Handling
--------------

Request Processing Errors
~~~~~~~~~~~~~~~~~~~~~~~~~

The callback handler catches and reports errors:

- JSON parsing errors return HTTP 500 with error details
- ProgressInfo creation errors return HTTP 500 with traceback
- Missing content-length header returns HTTP 200 (no processing)

Error responses include:

.. code-block:: text

    Error processing progress postback.
    EXCEPTION:
    <full traceback>


Forwarding Errors
~~~~~~~~~~~~~~~~~

Forwarding errors are handled gracefully:

- Network errors are logged but don't crash the server
- The forwarding loop continues after errors
- Errors are logged with full traceback for debugging


Best Practices
--------------

1. **Use unique task IDs** - Generate UUIDs for each task to ensure proper tracking
2. **Report completion** - Always send a ``Completed`` status when tasks finish
3. **Include worker metadata** - Use the ``data`` field to include worker identification
4. **Configure appropriate intervals** - Balance responsiveness with network overhead
5. **Secure forwarding endpoints** - Use authentication headers for production deployments
6. **Monitor forwarding errors** - Check logs for forwarding failures


Example Files
-------------

Complete working examples are available in the ``source/examples/`` directory:

- ``debug_concentrator_server.py`` - Starting a concentrator server
- ``debug_worker_progress.py`` - Submitting progress from workers
- ``debug_summary_forwarding.py`` - Configuring summary forwarding

