import subprocess
from typing import Union, List, Optional

from janis_core import Logger

from janis_assistant.templates.slurm import SlurmSingularityTemplate


class SpartanTemplate(SlurmSingularityTemplate):
    """
    https://dashboard.hpc.unimelb.edu.au/
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
        "janis_memory",
    ]

    def __init__(
        self,
        # General slurm
        sbatch: str = "sbatch",
        queues: Union[str, List[str]] = "physical",
        max_cores=32,
        max_ram=508,
        send_job_emails=True,
        catch_slurm_errors=True,
        # for submission
        submission_queue: str = None,
        submission_cpus: int = None,
        submission_memory: int = None,
        submission_node: str = None,
        max_workflow_time: int = 43000,
        # singularity
        container_dir: str = None,
        singularity_build_instructions=None,
        singularity_version="3.7.3",
        # janis specific
        mail_program="sendmail -t",
        intermediate_execution_dir: str = None,
    ):
        """Spartan template

        Template for Melbourne University's Spartan Slurm cluster

        :param intermediate_execution_dir: computation directory for intermediate files (defaults to <exec>/execution OR <outputdir>/janis/execution)
        :param queues: The queue to submit jobs to
        :param container_dir:
        :param singularity_version:
        :param send_job_emails: Send SLURM job emails to the listed email address
        :param catch_slurm_errors: Fail the task if Slurm kills the job (eg: memory / time)
        :param max_cores: Override maximum number of cores (default: 32)
        :param max_ram: Override maximum ram (default 508 [GB])
        """
        self.singularity_version = singularity_version

        singload = "module load singularity"
        if self.singularity_version:
            singload += "/" + str(self.singularity_version)

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
            run_in_background=True
        )

    def prejanis_hook(self) -> Optional[str]:
        """
        Before Janis starts to run a workflow, this block of code gets executed.
        If a string is returned, it is executed in the current environment. This
        block is also executed on a resume.

        This might be a good place to load relevant dependencies

        :return: str: bash script to run
        """
        return f"module load python/3.8.2 singularity/{self.singularity_version} java/11.0.2 web_proxy"
