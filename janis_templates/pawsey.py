import subprocess
from typing import Union, List

from janis_core import Logger

from janis_assistant.templates.slurm import SlurmSingularityTemplate


class PawseyTemplate(SlurmSingularityTemplate):
    """
    https://support.pawsey.org.au/documentation/display/US/Queue+Policies+and+Limits

    Template for Pawsey. This submits Janis to the longq cluster. There is currently NO support
    for workflows that run for longer than 4 days, though workflows can be resubmitted after this
    job dies.

    It's proposed that Janis assistant could resubmit itself
    """

    ignore_init_keys = [
        "intermediate_execution_dir",
        "build_instructions",
        "container_dir",
        "singularity_version",
        "singularity_build_instructions",
        "max_cores",
        "max_ram",
        "can_run_in_foreground",
        "run_in_background",
        "janis_memory",
    ]

    def __init__(
        self,
        container_dir: str,
        intermediate_execution_dir: str = None,
        queues: Union[str, List[str]] = "workq",
        singularity_version: str = "3.3.0",
        catch_slurm_errors=True,
        send_job_emails=True,
        singularity_build_instructions="singularity pull $image docker://${docker}",
        max_cores=28,
        max_ram=128,
        submission_queue: str = "longq",
        max_workflow_time: int = 5700,  # almost 4 days
        janis_memory_mb=None,
    ):
        """
        :param intermediate_execution_dir: A location where the execution should take place
        :param container_dir: Location where to save and execute containers from
        :param queues: A single or list of queues that woork should be submitted to
        :param singularity_version: Version of singularity to load
        :param catch_slurm_errors: Catch Slurm errors (like OOM or walltime)
        :param send_job_emails: (requires JanisConfiguration.notifications.email to be set) Send emails for mail types END
        :param singularity_build_instructions: Instructions for building singularity, it's recommended to not touch this setting.
        :param max_cores: Maximum number of cores a task can request
        :param max_ram: Maximum amount of ram (GB) that a task can request
        :param submission_queue: Queue to submit the janis 'brain' to
        """

        singload = "module load singularity"
        if singularity_version:
            singload += "/" + str(singularity_version)

        self.submission_queue = submission_queue
        self.max_workflow_time = max_workflow_time
        self.janis_memory_mb = janis_memory_mb

        super().__init__(
            intermediate_execution_dir=intermediate_execution_dir,
            queues=queues,
            container_dir=container_dir,
            catch_slurm_errors=catch_slurm_errors,
            send_job_emails=send_job_emails,
            build_instructions=singularity_build_instructions,
            singularity_load_instructions=singload,
            max_cores=max_cores,
            max_ram=max_ram,
        )

    def submit_detatched_resume(self, wid: str, command, logsdir, config, **kwargs):
        import os.path

        q = self.queues
        jq = ", ".join(q) if isinstance(q, list) else q
        jc = " ".join(command) if isinstance(command, list) else command
        newcommand = [
            "sbatch",
            "-p",
            self.submission_queue or jq,
            "-J",
            f"janis-{wid}",
            "--time",
            str(self.max_workflow_time or 5700),
            "-o",
            os.path.join(logsdir, "slurm.stdout"),
            "-e",
            os.path.join(logsdir, "slurm.stderr"),
        ]

        if (
            self.send_job_emails
            and config
            and config.notifications
            and config.notifications.email
        ):
            newcommand.extend(
                ["--mail-user", config.notifications.email, "--mail-type", "END"]
            )

        if self.janis_memory_mb:
            newcommand.extend(["--mem", str(self.janis_memory_mb)])

        newcommand.extend(["--wrap", jc])

        super().submit_detatched_resume(
            wid=wid,
            command=newcommand,
            capture_output=True,
            config=config,
            logsdir=logsdir,
            **kwargs,
        )
