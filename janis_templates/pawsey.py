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
        sbatch: str = "sbatch",
        queues: Union[str, List[str]] = "workq",
        send_job_emails=True,
        catch_slurm_errors=True,
        max_cores=28,
        max_ram=128,
        # for submission
        submission_queue: str = None,
        submission_cpus: int = None,
        submission_memory: int = None,
        submission_node: str = None,
        max_workflow_time: int = 43000,
        # singularity
        container_dir: str = None,
        singularity_build_instructions=None,
        singularity_version: str = "3.3.0",
        # janis specific
        mail_program="sendmail -t",
        intermediate_execution_dir: str = None,
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

        super().__init__(
            # slurm
            sbatch=sbatch,
            queues=queues,
            max_cores=max_cores,
            max_ram=max_ram,
            send_job_emails=send_job_emails,
            catch_slurm_errors=catch_slurm_errors,
            # submission
            submission_queue=submission_queue,
            submission_cpus=submission_cpus,
            submission_memory=submission_memory,
            submission_node=submission_node,
            max_workflow_time=max_workflow_time,
            # singularity
            container_dir=container_dir,
            build_instructions=singularity_build_instructions,
            singularity_load_instructions=singload,
            # janis-specific
            intermediate_execution_dir=intermediate_execution_dir,
            mail_program=mail_program,
        )
