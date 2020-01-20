import subprocess
from typing import Union, List

from janis_core import Logger

from janis_assistant.templates.slurm import SlurmSingularityTemplate


class SpartanTemplate(SlurmSingularityTemplate):
    """
    https://dashboard.hpc.unimelb.edu.au/
    """

    def __init__(
        self,
        container_dir: str,
        execution_dir: str = None,
        queues: Union[str, List[str]] = "cloud",
        singularity_version="3.2.0-spartan_gcc-6.2.0",
        send_job_emails=True,
        catch_slurm_errors=True,
        max_cores=32,
        max_ram=508,

        submission_queue: str = "cloud",
        max_workflow_time: int = 20100, # almost 14 days
    ):
        """Spartan template

        Template for Melbourne University's Spartan Slurm cluster

        :param execution_dir: execution directory for Cromwell
        :param queues: The queue to submit jobs to
        :param container_dir:
        :param singularity_version:
        :param send_job_emails: Send SLURM job emails to the listed email address
        :param catch_slurm_errors: Fail the task if Slurm kills the job (eg: memory / time)
        :param max_cores: Override maximum number of cores (default: 32)
        :param max_ram: Override maximum ram (default 508 [GB])
        """
        singload = "module load Singularity"
        if singularity_version:
            singload += "/" + str(singularity_version)

        self.submission_queue = submission_queue
        self.max_workflow_time = max_workflow_time

        super().__init__(
            mail_program="sendmail -t",
            execution_dir=execution_dir,
            container_dir=container_dir,
            queues=queues,
            send_job_emails=send_job_emails,
            catch_slurm_errors=catch_slurm_errors,
            build_instructions="singularity pull $image docker://${docker}",
            singularity_load_instructions=singload,
            limit_resources=False,
            max_cores=max_cores,
            max_ram=max_ram,
        )

    def submit_detatched_resume(self, wid, command, config, logsdir, **kwargs):
        import os.path
        q = self.submission_queue or self.queues or "physical"
        jq = ", ".join(q) if isinstance(q, list) else q
        jc = " ".join(command) if isinstance(command, list) else command
        loadedcommand = "module load Java && module load web_proxy && " + jc
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
            self.send_slurm_emails
            and config
            and config.notifications
            and config.notifications.email
        ):
            newcommand.extend(
                ["--mail-user", config.notifications.email, "--mail-type", "END"]
            )

        newcommand.extend(["--wrap", loadedcommand])

        super().submit_detatched_resume(
            wid=wid,
            command=newcommand,
            capture_output=True,
            config=config,
            logsdir=logsdir,
            **kwargs,
        )
