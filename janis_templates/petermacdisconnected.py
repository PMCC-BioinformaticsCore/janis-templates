import subprocess
from typing import Union, List

from janis_core import Logger

from .petermac import PeterMacTemplate


class PeterMacDisconnectedTemplate(PeterMacTemplate):
    def __init__(
        self,
        execution_dir: str = None,
        queues: Union[str, List[str]] = "prod_med,prod",
        container_dir: str = "/config/binaries/singularity/containers_devel/janis/",
        singularity_version: bool = "3.4.0",
        catch_slurm_errors: bool = True,
        send_job_emails: bool = False,
        max_cores=40,
        max_ram=256,
        max_workflow_time: int = 14400,
    ):

        buildinstructions = (
            f"unset SINGULARITY_TMPDIR && docker_subbed=$(sed -e 's/[^A-Za-z0-9._-]/_/g' <<< ${{docker}}) "
            f"&& image={container_dir}/$docker_subbed.sif && singularity pull $image docker://${{docker}}"
        )

        super().__init__(
            execution_dir=execution_dir,
            queues=queues,
            container_dir=container_dir,
            singularity_version=singularity_version,
            catch_slurm_errors=catch_slurm_errors,
            singularity_build_instructions=buildinstructions,
            send_job_emails=send_job_emails,
            max_cores=max_cores,
            max_ram=max_ram,
        )

        self.max_workflow_time = max_workflow_time

    def submit_detatched_resume(
        self, wid: str, command: List[str], logsdir, config, **kwargs
    ):
        import os.path

        q = "janis"
        jq = ", ".join(q) if isinstance(q, list) else q
        jc = " ".join(command) if isinstance(command, list) else command

        newcommand = [
            "sbatch",
            "-p",
            jq,
            "-J",
            f"janis-{wid}",
            "--time",
            str(self.max_workflow_time or 1440),
            "-o",
            os.path.join(logsdir, "slurm.stdout"),
            "-e",
            os.path.join(logsdir, "slurm.stderr"),
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

        newcommand.extend(["--wrap", jc])

        super().submit_detatched_resume(
            wid=wid,
            command=newcommand,
            capture_output=True,
            config=config,
            logsdir=logsdir,
            **kwargs,
        )
