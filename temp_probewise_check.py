# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import uuid
import json
from colorama import Fore, Style
from garak import _config, _plugins
from garak.harnesses.base import Harness

logger = logging.getLogger(__name__)


class OutputMock:
    def __init__(self, text):
        self.text = text if isinstance(text, str) else str(text)
        self.prompt = self.text
        self.status = "success"
        self.lang = "en"
        self.data_path = None
        self.data_type = None
        self.data_checksum = None
        self.notes = None


class AttemptMock:
    def __init__(self, outputs, probename, prompt=None, seq=0):
        self.all_outputs = [
            OutputMock(output)
            for output in (outputs if isinstance(outputs, list) else [outputs])
        ]
        self.probename = probename
        self.probe_classname = ".".join(
            probename.split(".")[1:]
        )  # Changed to "category.Class" format, e.g., "xss.ColabAIDataLeakage"
        self.prompt = (
            prompt
            if prompt
            else {
                "turns": [
                    {
                        "role": "user",
                        "content": {"text": prompt or "", "lang": "en", "notes": {}},
                    }
                ]
            }
        )
        self.status = "success"
        self.detector_results = {}
        self.notes = {"terms": ["summary", "conversation"]}
        self.outputs = [output.text for output in self.all_outputs]
        self.uuid = str(uuid.uuid4())
        self.seq = seq
        self.probe_params = {}
        self.targets = []
        self.conversations = [
            {
                "turns": [
                    {
                        "role": "user",
                        "content": {"text": prompt or "", "lang": "en", "notes": {}},
                    },
                    {
                        "role": "assistant",
                        "content": {"text": output.text, "lang": "en", "notes": {}},
                    },
                ]
            }
            for output in self.all_outputs
        ]
        self.reverse_translation_outputs = []


class ProbewiseHarness(Harness):
    def _load_detector(self, detector_name: str):
        logger.debug(f"Attempting to load detector: {detector_name}")
        try:
            detector = _plugins.load_plugin(
                "detectors." + detector_name, break_on_fail=False
            )
            if detector:
                logger.debug(f"Successfully loaded detector: {detector_name}")
                return detector
            else:
                logger.error(f"Detector load failed: {detector_name}, skipping")
                print(f"Error: Detector {detector_name} failed to load, skipping")
        except Exception as e:
            logger.error(f"Exception loading detector {detector_name}: {str(e)}")
            print(f"Error: Failed to load detector {detector_name}: {str(e)}")
        return None

    def run(self, model, probenames, evaluator, buff_names=None):
        if buff_names is None:
            buff_names = []

        self._load_buffs(buff_names)
        probenames = sorted(probenames)

        # RESUME SUPPORT: Initialize or resume run
        from garak import resumeservice

        logger.info(f"Resume setup: enabled={resumeservice.enabled()}, resumable={_config.run.resumable}")
        if not resumeservice.enabled():
            # New run - initialize if resumable
            if _config.run.resumable:
                logger.info(f"Initializing new resumable run with granularity={resumeservice.get_granularity()}")
                run_id = resumeservice.initialize_new_run(probenames, model)
                granularity = resumeservice.get_granularity()
                logger.info(f"Initialized run {run_id} with granularity={granularity}")
                print(
                    f"🆔 Run ID: {run_id} ({granularity}-level resume enabled)"
                )
                print(f"   Use --resume {run_id} to continue if interrupted")
        else:
            # Resume mode - load the state
            logger.info(f"Loading resume state for run {_config.transient.resume_run_id}")
            resumeservice.load()
            symbol, msg = resumeservice.start_msg()
            if msg:
                print(f"{symbol} {msg}")

        print(
            f"🕵️ queue of {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}probes:{Style.RESET_ALL} "
            + ", ".join([name.replace("probes.", "") for name in probenames])
        )

        for probename in probenames:
            # RESUME SUPPORT: Skip completed probes in BOTH probe and attempt-level granularity
            # A completed probe means ALL its attempts are done, so always skip it
            if resumeservice.should_skip_probe(probename):
                logger.info(f"Skipping completed probe: {probename}")
                print(f"⏭️  Skipping completed: {probename}")
                continue

            logger.debug(f"Loading probe: {probename}")
            probe = _plugins.load_plugin(probename)
            if not probe:
                logger.warning(f"Probe {probename} failed to load, skipping")
                print(f"failed to load probe {probename}")
                continue

            detectors = []
            if probe.primary_detector:
                d = self._load_detector(probe.primary_detector)
                if d:
                    detectors.append(d)
                else:
                    logger.warning(
                        f"Primary detector {probe.primary_detector} failed for {probename}"
                    )
                if _config.plugins.extended_detectors is True:
                    for detector_name in sorted(probe.extended_detectors):
                        d = self._load_detector(detector_name)
                        if d:
                            detectors.append(d)
                        else:
                            logger.warning(
                                f"Extended detector {detector_name} failed for {probename}"
                            )
            else:
                logger.debug(
                    "deprecation warning - probe %s using recommended_detector instead of primary_detector",
                    probename,
                )
                for detector_name in sorted(probe.recommended_detector):
                    d = self._load_detector(detector_name)
                    if d:
                        detectors.append(d)
                    else:
                        logger.warning(
                            f"Recommended detector {detector_name} failed for {probename}"
                        )

            if not detectors:
                logger.error(f"No detectors loaded for {probename}, skipping")
                print(f"Error: No detectors loaded for {probename}, skipping")
                continue

            logger.info(
                f"Running probe {probename} with detectors: {[d.__class__.__name__ for d in detectors]}"
            )
            print(
                f"Running probe {probename} with detectors: {[d.__class__.__name__ for d in detectors]}"
            )

            # RESUME SUPPORT: For attempt-level granularity, check if probe is already complete BEFORE generating attempts
            # This prevents unnecessary HTTP calls for completed probes
            probe_short_name = probename.replace("probes.", "")
            if resumeservice.get_granularity() == "attempt":
                # Check if we have saved state for this probe
                saved_probe_state = resumeservice.get_probe_state(probe_short_name)
                if saved_probe_state:
                    resume_point = saved_probe_state.get("prompt_index", -1) + 1
                    total_prompts_saved = saved_probe_state.get("total_prompts", 0)
                    
                    # If all attempts were completed, skip this probe entirely
                    if resume_point >= total_prompts_saved and total_prompts_saved > 0:
                        logger.info(f"All {total_prompts_saved} attempts for {probename} already completed (from saved state), skipping probe")
                        print(f"✅ All {total_prompts_saved} attempts for {probename} already completed")
                        # Mark probe as complete and continue to next probe
                        resumeservice.mark_probe_complete(probename)
                        continue

            try:
                logger.info(f"Calling probe.probe() for {probename}")
                attempts = probe.probe(model)
                logger.info(f"probe.probe() returned for {probename}")
                if not attempts:
                    logger.error(f"Probe {probename} returned no attempts, skipping")
                    print(f"Probe {probename} returned no attempts, skipping")
                    continue

                # Convert to list to get total count
                attempts = list(attempts)
                total_prompts = len(attempts)
                probe_short_name = probename.replace("probes.", "")
                logger.info(f"Probe {probename} generated {total_prompts} total attempts")

                # RESUME SUPPORT: Filter out completed attempts if using attempt-level granularity
                if resumeservice.get_granularity() == "attempt":
                    resume_point = resumeservice.get_resume_point(probe_short_name)
                    logger.info(f"Resume point for {probe_short_name}: {resume_point}/{total_prompts}")
                    
                    if resume_point >= total_prompts:
                        logger.info(f"All attempts for {probename} already completed, skipping probe")
                        print(f"✅ All attempts for {probename} already completed")
                        # Mark probe as complete if all its attempts are done
                        resumeservice.mark_probe_complete(probename)
                        continue
                    
                    if resume_point > 0:
                        logger.info(f"Resuming {probename} from prompt {resume_point}/{total_prompts}")
                        print(f"⏭️  Resuming {probename} from attempt {resume_point + 1}/{total_prompts} (skipping {resume_point} completed)")
                    
                    # Filter attempts to only process from resume_point onwards
                    attempts = [a for a in attempts if a.seq >= resume_point]
                    
                    if not attempts:
                        logger.info(f"All attempts for {probename} already completed, skipping probe")
                        print(f"✅ All attempts for {probename} already completed")
                        resumeservice.mark_probe_complete(probename)
                        continue

                #Evaluate attempts with detectors - use original interface that passes Attempt objects
                probe_category = (
                    probename.split(".")[1]
                    if len(probename.split(".")) > 1
                    else probename
                )
                probe_short_name = probename.replace("probes.", "")
                # FIXED: Collect attempts with detector results for evaluator
                attempts_with_results = []
                for attempt in attempts:
                    for detector in detectors:
                        logger.debug(
                            f"Evaluating with detector {detector.__class__.__name__}"
                        )
                        detector_module = detector.__class__.__module__.split(".")[-1]
                        detector_key = (
                            f"{detector_module}.{detector.__class__.__name__}"
                        )

                        # FIXED: Use original detector interface - pass Attempt object, not individual outputs
                        try:
                            # Pass the full Attempt object to the detector (original Garak behavior)
                            detector_result = detector.detect(attempt)

                            # Store the result - convert to list if needed
                            if not hasattr(attempt, "detector_results"):
                                attempt.detector_results = {}
                            # Ensure detector_result is a list
                            if not isinstance(detector_result, list):
                                detector_result = list(detector_result)
                            attempt.detector_results[detector_key] = detector_result

                            logger.debug(
                                f"Detector {detector.__class__.__name__} result for {detector_key}: {detector_result}"
                            )

                        except Exception as det_e:
                            logger.error(
                                f"Detector {detector.__class__.__name__} failed for {probename}: {det_e}"
                            )
                            if hasattr(attempt, "all_outputs") and attempt.all_outputs:
                                attempt.detector_results[detector_key] = [0.0] * len(
                                    attempt.all_outputs
                                )
                            else:
                                attempt.detector_results[detector_key] = [0.0]
                    
                    # Add attempt to list for evaluator after all its detectors complete
                    attempts_with_results.append(attempt)
                    
                    # RESUME SUPPORT: Write attempt to report immediately after all its detectors complete
                    # This allows incremental resume - if interrupted, completed attempts are already saved
                    try:
                        # Prefer using as_dict() if available
                        if hasattr(attempt, "as_dict"):
                            d = attempt.as_dict()
                        else:
                            d = {
                                "entry_type": "attempt",
                                "uuid": getattr(attempt, "uuid", ""),
                                "seq": getattr(attempt, "seq", 0),
                                "status": getattr(attempt, "status", 1),
                                "probe_classname": (
                                    ".".join(probename.split(".")[1:])
                                    if probename
                                    else ""
                                ),
                                "probe_params": getattr(attempt, "probe_params", {}),
                                "targets": getattr(attempt, "targets", []),
                                "prompt": getattr(attempt, "prompt", {}),
                                "outputs": getattr(attempt, "outputs", []),
                                "detector_results": getattr(
                                    attempt, "detector_results", {}
                                ),
                                "notes": getattr(attempt, "notes", {}),
                                "goal": getattr(attempt, "goal", None),
                                "conversations": getattr(attempt, "conversations", []),
                                "reverse_translation_outputs": getattr(
                                    attempt, "reverse_translation_outputs", []
                                ),
                            }

                        # Set status to 2 (post-evaluation)
                        d["status"] = 2

                        try:
                            from garak.serializers import normalize_attempt_for_persistence
                            normalize_attempt_for_persistence(d)
                        except Exception:
                            pass

                        _config.transient.reportfile.write(
                            json.dumps(d, ensure_ascii=False) + "\n"
                        )
                        _config.transient.reportfile.flush()
                        
                        # RESUME SUPPORT: Save prompt-level progress after each attempt
                        granularity = resumeservice.get_granularity()
                        logger.debug(f"After writing attempt {attempt.seq}, checking granularity: {granularity}")
                        if granularity == "attempt":
                            logger.info(f"Saving progress for probe {probe_short_name}, attempt {attempt.seq}/{total_prompts}")
                            # Save progress with prompt_index (seq) and total_prompts
                            resumeservice.save_probe_progress(
                                probe_short_name, 
                                attempt.seq,  # Last completed prompt index
                                total_prompts  # Total prompts for this probe
                            )
                            # Also mark attempt complete for backwards compatibility
                            logger.debug(f"Marking attempt {attempt.seq} complete for {probe_short_name}")
                            resumeservice.mark_attempt_complete_by_seq(probe_short_name, attempt.seq)
                            logger.info(f"✅ Saved attempt {attempt.seq} for {probe_short_name}")
                            print(f"  💾 Saved progress: attempt {attempt.seq + 1}/{total_prompts}")
                        else:
                            logger.debug(f"Skipping attempt-level save because granularity is '{granularity}', not 'attempt'")
                            
                    except Exception as write_e:
                        logger.exception(
                            f"Failed to write attempt entry for probe {probename}: {write_e}"
                        )

                # Pass attempts to evaluator after all attempts are written
                logger.debug(
                    f"Calling evaluator.evaluate for {probename} with {len(attempts_with_results)} attempts"
                )
                # Set evaluator.probename to module.class format
                evaluator.probename = (
                    probename  # Changed to probename for report compatibility
                )
                evaluator.evaluate(attempts_with_results)
                logger.debug(
                    f"Evaluated attempts for {probename}: {[attempt.detector_results for attempt in attempts_with_results]}"
                )

                logger.info(f"Probe {probename} executed successfully")

                # RESUME SUPPORT: Mark probe complete
                from garak import resumeservice

                resumeservice.mark_probe_complete(probename)

            except Exception as e:
                logger.error(
                    f"Error or interruption during probe {probename}: {str(e)}"
                )
                print(f"Error or interruption during probe {probename}: {str(e)}")
                raise

        # RESUME SUPPORT: Mark run complete after all probes finish
        from garak import resumeservice

        resumeservice.mark_run_complete()
