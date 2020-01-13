import subprocess
from typing import Union, List

from janis_core import Logger

from .petermac import PeterMacTemplate


class PeterMacDisconnectedTemplate(PeterMacTemplate):
    def __init__(
        self,
        executionDir: str=None,
        queues: Union[str, List[str]] = "prod_med,prod",
        containerDir: str="/config/binaries/singularity/containers_devel/janis/",
        singularityVersion: bool="3.4.0",
        catchSlurmErrors: bool=True,
        sendSlurmEmails: bool=False,
        max_workflow_time: int=14400
    ):

        buildinstructions = (
            f"unset SINGULARITY_TMPDIR && docker_subbed=$(sed -e 's/[^A-Za-z0-9._-]/_/g' <<< ${{docker}}) "
            f"&& image={containerDir}/$docker_subbed.sif && singularity pull $image docker://${{docker}}"
        )

        super().__init__(
            executionDir=executionDir,
            queues=queues,
            containerDir=containerDir,
            singularityVersion=singularityVersion,
            catchSlurmErrors=catchSlurmErrors,
            sendSlurmEmails=sendSlurmEmails,
            singularityBuildInstructions=buildinstructions,
        )

        self.max_workflow_time = max_workflow_time

    def submit_detatched_resume(
        self, wid: str, command: List[str], logsdir, **kwargs
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
            "-o", os.path.join(logsdir, "slurm.stdout"),
            "-e", os.path.join(logsdir, "slurm.stderr"),
            "--wrap",
            jc,
        ]
        super().__init__(wid=wid, command=newcommand, capture_output=True, **kwargs)