Resuming Interrupted Scans
=========================

garak supports resuming interrupted vulnerability scans, allowing you to continue 
long-running assessments after network issues, system restarts, or manual interruptions.

Overview
--------

The resume feature enables you to:

* **Resume interrupted scans** from where they left off
* **Choose granularity**: skip entire probes or individual attempts
* **Manage scan state** with list and delete operations
* **Preserve report continuity** across resume sessions

Quick Start
-----------

Make a Scan Resumable
~~~~~~~~~~~~~~~~~~~~~

Add the ``--resumable`` flag to enable resume for your scan:

.. code-block:: bash

   garak --target_type openai --target_name gpt-4 --resumable --probes all

If the scan is interrupted, you'll see a message with the run ID:

.. code-block:: text

   Scan interrupted. Resume with:
   garak --resume garak-run-abc123-20240123-103000

Resume a Scan
~~~~~~~~~~~~

Use the run ID to resume:

.. code-block:: bash

   garak --resume garak-run-abc123-20240123-103000

The scan will continue from where it stopped.

List Resumable Runs
~~~~~~~~~~~~~~~~~~

View all resumable scans:

.. code-block:: bash

   garak --list_runs

Output:

.. code-block:: text

   Resumable runs:
   
   1. garak-run-abc123-20240123-103000
      Started: 2024-01-23 10:30:00
      Progress: 5/10 probes complete (50%)
      Target: openai/gpt-4
      
   2. garak-run-def456-20240122-153000
      Started: 2024-01-22 15:30:00
      Progress: 23/50 probes complete (46%)
      Target: huggingface/llama-2-7b

Granularity Levels
------------------

Resume granularity controls how precisely garak resumes your scan.

Attempt-Level (Default)
~~~~~~~~~~~~~~~~~~~~~~~

**Most precise**: Skips individual completed prompts.

.. code-block:: bash

   garak --resumable --resume_granularity attempt

**Use when**:

* Maximum precision is needed
* Individual attempts take significant time
* You want to resume at the exact interruption point

**Characteristics**:

* ✅ **Precise**: Resumes from exact prompt
* ✅ **Efficient**: No wasted computation
* ⚠️ **Slower**: Per-attempt checks
* ⚠️ **Larger state**: More storage needed

Probe-Level
~~~~~~~~~~~

**Faster**: Skips entire completed probes.

.. code-block:: bash

   garak --resumable --resume_granularity probe

**Use when**:

* Quick resume is sufficient
* Interrupted near the end of a probe
* Storage is constrained

**Characteristics**:

* ✅ **Fast**: Minimal overhead
* ✅ **Small state**: Less storage
* ⚠️ **Coarse**: May re-run some attempts
* ⚠️ **Less precise**: Resumes at probe boundaries

Comparison
~~~~~~~~~~

+-------------------+------------------+-------------+
| Feature           | Attempt-Level    | Probe-Level |
+===================+==================+=============+
| Precision         | Exact prompt     | Entire probe|
+-------------------+------------------+-------------+
| Resume Speed      | Moderate         | Fast        |
+-------------------+------------------+-------------+
| State Size        | ~5 MB            | ~50 KB      |
+-------------------+------------------+-------------+
| Overhead          | Per-attempt      | Minimal     |
+-------------------+------------------+-------------+
| Best For          | Long probes      | Quick resume|
+-------------------+------------------+-------------+

Configuration
-------------

Via Command Line
~~~~~~~~~~~~~~~~

.. code-block:: bash

   garak --resumable \
         --resume_granularity attempt \
         --target_type openai \
         --target_name gpt-4 \
         --probes dan,encoding

Via Configuration File
~~~~~~~~~~~~~~~~~~~~~~

Create ``garak.site.yaml``:

.. code-block:: yaml

   run:
     resumable: true
     resume_granularity: attempt

Then run normally:

.. code-block:: bash

   garak --target_type openai --target_name gpt-4 --probes all

Run Management
--------------

Delete Run State
~~~~~~~~~~~~~~~~

Remove old run state to free storage:

.. code-block:: bash

   garak --delete_run garak-run-abc123-20240123-103000

**Warning**: This permanently deletes resume state. The run cannot be resumed afterward.

State Storage
~~~~~~~~~~~~~

Resume state is stored in:

.. code-block:: text

   ~/.garak/runs/<run-id>/state.json

Each run's state includes:

* Run ID and timestamps
* Probe list and progress
* Completed attempts (attempt-level)
* Version information

How It Works
------------

Resume Process
~~~~~~~~~~~~~~

1. **State Initialization**: When you run with ``--resumable``, garak creates a state file
2. **Progress Tracking**: As probes complete, state is saved
3. **Interruption**: If interrupted, state preserves progress
4. **Resume**: Use ``--resume`` to load state and continue

UUID-Based Tracking
~~~~~~~~~~~~~~~~~~~

Each attempt gets a unique UUID for reliable identification:

.. code-block:: python

   attempt.uuid = "123e4567-e89b-12d3-a456-426614174000"

This is more robust than text-based prompt matching because:

* ✅ Survives prompt modifications (buffing)
* ✅ Works with multi-modal inputs
* ✅ No ambiguity with similar prompts

Report Continuity
~~~~~~~~~~~~~~~~~

Resumed scans maintain report integrity:

* Original ``run_id`` preserved
* Original ``start_time`` retained
* Single final digest (old ones removed)
* No duplicate attempts

Probe Resumability
------------------

Most probes support resume, but some have complex internal state:

Resumable Probes
~~~~~~~~~~~~~~~~

* Standard probes (``garak.probes.Probe``)
* Most probe families (dan, encoding, lmrc, etc.)

Non-Resumable Probes
~~~~~~~~~~~~~~~~~~~~

* ``TreeSearchProbe``: Maintains search trees
* ``IterativeProbe``: Multi-turn conversations

These probes run from start even when resuming.

Examples
--------

Example 1: Resume After Network Interruption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start a long scan
   garak --target_type openai --target_name gpt-4 --resumable --probes all
   
   # ... network interrupts ...
   # Output: Resume with: garak --resume garak-run-abc123-...
   
   # Resume when network returns
   garak --resume garak-run-abc123-20240123-103000

Example 2: Resume with Different Granularity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start with attempt-level precision
   garak --resumable --resume_granularity attempt --target_type openai

   # ... interrupt ...

   # Resume with probe-level for faster completion
   # (NOTE: Granularity is locked at run creation time)
   garak --resume garak-run-abc123-20240123-103000

Example 3: Manage Multiple Runs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all runs
   garak --list_runs
   
   # Resume a specific run
   garak --resume garak-run-abc123-20240123-103000
   
   # Delete old runs
   garak --delete_run garak-run-old-20240120-100000

Troubleshooting
---------------

Version Mismatch
~~~~~~~~~~~~~~~~

**Error**: ``Version mismatch: run created with garak 0.9.0, current version is 0.9.1``

**Solution**: 
1. Try resuming anyway (may work)
2. If it fails, delete run and start fresh

Corrupted State
~~~~~~~~~~~~~~~

**Error**: ``Corrupted state file for run ...``

**Solution**: Delete the run state and start a new scan:

.. code-block:: bash

   garak --delete_run garak-run-corrupted-...

Missing Run
~~~~~~~~~~~

**Error**: ``No run found with ID: ...``

**Solution**: Check available runs:

.. code-block:: bash

   garak --list_runs

Best Practices
--------------

1. **Use attempt-level by default**: More precise, worth the overhead
2. **Delete old runs**: Free up disk space when scans are complete
3. **Monitor progress**: Use ``--list_runs`` to check scan status
4. **Version consistency**: Resume with same garak version when possible

Performance Tips
~~~~~~~~~~~~~~~~

* **Probe-level** for nearly-complete scans (last 10-20% of probes)
* **Attempt-level** for expensive probes (API-based, compute-intensive)
* **Regular cleanup**: Delete old run state monthly

Limitations
-----------

* **No checkpoint resume**: Only resumes from completed attempts/probes
* **No distributed resume**: Single-machine only
* **Version sensitive**: Best with same garak version

Future Enhancements
-------------------

Planned features:

* Automatic crash detection and resume
* Checkpoint-based resume (save state every N attempts)
* Distributed resume across multiple workers
* Web UI for run management

API Documentation
-----------------

For programmatic access, see:

* :doc:`garak.resumeservice <resumeservice>` - Resume service module
* :doc:`garak.probes.base <garak.probes.base>` - Probe resumability

See Also
--------

* :doc:`CLI Reference <cliref>` - Full command-line options
* :doc:`Configuring garak <configurable>` - Configuration files
* :doc:`Probes <probes>` - Probe documentation
