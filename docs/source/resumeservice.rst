garak.resumeservice
===================

The ``resumeservice`` module provides state management for resuming interrupted garak scans.
It follows the service pattern established by ``langservice`` and supports configurable 
granularity at both probe-level and attempt-level.

Overview
--------

The resume service enables:

* **State Persistence**: Saves scan progress to ``~/.garak/runs/<run_id>/state.json``
* **UUID-Based Tracking**: Robust identification of completed attempts
* **Configurable Granularity**: Choose between probe-level (fast) or attempt-level (precise)
* **Run Management**: List, resume, and delete operations for scan state

Architecture
------------

Service Pattern
~~~~~~~~~~~~~~~

The module follows garak's service pattern with:

* Module-level state management
* Lazy initialization
* Clean separation from core logic
* Optional/opt-in activation

State Storage
~~~~~~~~~~~~~

State is stored separately from reports in:

.. code-block:: text

   ~/.garak/runs/
   └── garak-run-<uuid>-<timestamp>/
       ├── state.json       # Scan progress
       └── metadata.json    # Run metadata

Granularity Levels
~~~~~~~~~~~~~~~~~~

**Probe-Level** (Default)
   * Tracks completed probes
   * Fast resume with minimal overhead
   * ~50 KB state size
   * Best for quick iterations

**Attempt-Level**
   * Tracks individual completed attempts
   * Precise resume at exact interruption point
   * ~5 MB state size
   * Best for long-running probes

Configuration
-------------

Via Command Line
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Enable resumable scan
   garak --resumable --probes all

   # Set granularity
   garak --resumable --resume_granularity attempt

   # Resume a scan
   garak --resume garak-run-abc123-20260123-103000

   # List resumable runs
   garak --list_runs

   # Delete a run
   garak --delete_run garak-run-abc123-20260123-103000

Via Configuration File
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   run:
     resumable: true
     resume_granularity: attempt  # or 'probe'

Via Environment Variable
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   export GARAK_RESUME_GRANULARITY=attempt

API Reference
-------------

Service Control Functions
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: garak.resumeservice.enabled

.. autofunction:: garak.resumeservice.load

.. autofunction:: garak.resumeservice.get_state

.. autofunction:: garak.resumeservice.get_granularity

Run Management Functions
~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: garak.resumeservice.initialize_new_run

.. autofunction:: garak.resumeservice.mark_run_complete

.. autofunction:: garak.resumeservice.list_runs

.. autofunction:: garak.resumeservice.delete_run

Probe Integration Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: garak.resumeservice.is_probe_resumable

.. autofunction:: garak.resumeservice.should_skip_probe

.. autofunction:: garak.resumeservice.mark_probe_complete

.. autofunction:: garak.resumeservice.get_resume_point

Attempt Tracking Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: garak.resumeservice.is_attempt_complete

.. autofunction:: garak.resumeservice.mark_attempt_complete

.. autofunction:: garak.resumeservice.update_probe_progress

Utility Functions
~~~~~~~~~~~~~~~~~

.. autofunction:: garak.resumeservice.get_run_id

.. autofunction:: garak.resumeservice.get_current_run_id

.. autofunction:: garak.resumeservice.extract_uuid_from_run_id

Classes
-------

RunManager
~~~~~~~~~~

.. autoclass:: garak.resumeservice.RunManager
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from garak import resumeservice
   
   # Check if resume is enabled
   if resumeservice.enabled():
       state = resumeservice.get_state()
       print(f"Resuming run: {state['run_id']}")
   
   # Check granularity
   granularity = resumeservice.get_granularity()
   print(f"Using {granularity}-level tracking")

Probe Integration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from garak import resumeservice
   
   # Check if probe should be skipped
   if resumeservice.should_skip_probe("dan.Dan_11_0"):
       print("Probe already completed, skipping...")
       return
   
   # Get resume point for attempt-level
   if resumeservice.get_granularity() == "attempt":
       resume_point = resumeservice.get_resume_point("dan.Dan_11_0")
       prompts = prompts[resume_point:]  # Skip completed attempts

Custom State Management
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from garak import resumeservice
   
   # Initialize new resumable run
   run_id = resumeservice.initialize_new_run(
       probenames=["dan", "encoding"],
       generator=my_generator
   )
   
   # Mark probe complete
   resumeservice.mark_probe_complete("dan.Dan_11_0")
   
   # Mark run complete
   resumeservice.mark_run_complete()

See Also
--------

* :doc:`resuming` - User guide for resuming scans
* :doc:`cli` - CLI reference for resume commands
* :doc:`configurable` - Configuration options
* :doc:`probes` - Probe documentation
* :doc:`harnesses` - Harness documentation

Notes
-----

**Probe Compatibility**

Most probes support resume functionality automatically. Probes with complex 
internal state (like ``TreeSearchProbe`` and ``IterativeProbe``) set 
``supports_resume = False`` and run from the beginning each time.

**State Safety**

The resume service uses atomic file writes to prevent state corruption:

1. Writes to temporary file
2. Verifies JSON validity
3. Atomic rename to final location

**Performance Considerations**

* **Probe-level**: Minimal overhead, ~1ms per probe check
* **Attempt-level**: ~5-10ms per attempt check with UUID comparison
* State file size grows linearly with attempts tracked

**Cleanup**

Old run states are not automatically deleted. Use ``--list_runs`` to view 
and ``--delete_run`` to clean up old state files.
