import subprocess
from typing import Union, List

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
        "run_in_background",
        "janis_memory",
    ]

    def __init__(
        self,
        container_dir: str,
        intermediate_execution_dir: str = None,
        queues: Union[str, List[str]] = "physical",
        singularity_version="3.5.3",
        send_job_emails=True,
        catch_slurm_errors=True,
        max_cores=32,
        max_ram=508,
        submission_queue: str = "physical",
        max_workflow_time: int = 20100,  # almost 14 days
        janis_memory_mb=None,
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
        singload = "module load singularity"
        if singularity_version:
            singload += "/" + str(singularity_version)

        self.submission_queue = submission_queue
        self.max_workflow_time = max_workflow_time
        self.janis_memory_mb = janis_memory_mb

        super().__init__(
            mail_program="sendmail -t",
            intermediate_execution_dir=intermediate_execution_dir,
            container_dir=container_dir,
            queues=queues,
            send_job_emails=send_job_emails,
            catch_slurm_errors=catch_slurm_errors,
            build_instructions="singularity pull $image docker://${docker}",
            singularity_load_instructions=singload,
            max_cores=max_cores,
            max_ram=max_ram,
        )

    def submit_detatched_resume(self, wid, command, config, logsdir, **kwargs):
        import os.path

        q = self.submission_queue or self.queues or "physical"
        jq = ", ".join(q) if isinstance(q, list) else q
        jc = " ".join(command) if isinstance(command, list) else command
        loadedcommand = "module load java && module load web_proxy && " + jc
        newcommand = [
            "sbatch",
            "-p",
            jq,
            "-J",
            f"janis-{wid}",
            "-o",
            os.path.join(logsdir, "slurm.stdout"),
            "-e",
            os.path.join(logsdir, "slurm.stderr"),
            "--time",
            str(self.max_workflow_time or 20100),
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

        newcommand.extend(["--wrap", loadedcommand])

        super().submit_detatched_resume(
            wid=wid,
            command=newcommand,
            capture_output=True,
            config=config,
            logsdir=logsdir,
            **kwargs,
        )
