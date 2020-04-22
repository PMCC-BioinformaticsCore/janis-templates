from typing import Union, List

from janis_assistant.templates.slurm import SlurmSingularityTemplate


class PeterMacTemplate(SlurmSingularityTemplate):

    ignore_init_keys = [
        "execution_dir",
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
        execution_dir: str = None,
        container_dir="/config/binaries/singularity/containers_devel/janis/",
        queues: Union[str, List[str]] = "prod_med,prod",
        singularity_version="3.4.0",
        send_job_emails=False,
        catch_slurm_errors=True,
        singularity_build_instructions=None,
        max_cores=40,
        max_ram=256,
        max_workflow_time: int = 20100,  # almost 14 days
        janis_memory_mb=None,
    ):
        """Peter Mac (login node) template

        Template to run Janis / Cromwell at the Peter MacCallum Cancer Centre (Rosalind)

        :param execution_dir: Execution directory
        :param queues: The queue to submit jobs to
        :param container_dir: [OPTIONAL] Override the directory singularity containers are stored in
        :param singularity_version: The version of Singularity to use on the cluster
        :param send_job_emails: Send Slurm job notifications using the provided email
        :param catch_slurm_errors: Fail the task if Slurm kills the job (eg: memory / time)
        :param singularity_build_instructions: Sensible default for PeterMac template
        :param max_cores: Override maximum number of cores (default: 32)
        :param max_ram: Override maximum ram (default 508 [GB])
        :param max_workflow_time: The walltime of the submitted workflow "brain"
        """

        singload = "module load singularity"
        if singularity_version:
            singload += "/" + str(singularity_version)

        joined_queued = ",".join(queues) if isinstance(queues, list) else str(queues)

        # Very cromwell specific at the moment, need to generalise this later
        if not singularity_build_instructions:
            singularity_build_instructions = f"sbatch -p {joined_queued} --wait \
    --wrap 'unset SINGULARITY_TMPDIR && docker_subbed=$(sed -e 's/[^A-Za-z0-9._-]/_/g' <<< ${{docker}}) \
    && image={container_dir}/$docker_subbed.sif && singularity pull $image docker://${{docker}}'"

        self.max_workflow_time = max_workflow_time
        self.janis_memory_mb = janis_memory_mb

        super().__init__(
            mail_program="sendmail -t",
            execution_dir=execution_dir,
            container_dir=container_dir,
            queues=joined_queued,
            send_job_emails=send_job_emails,
            catch_slurm_errors=catch_slurm_errors,
            build_instructions=singularity_build_instructions,
            singularity_load_instructions=singload,
            max_cores=max_cores,
            max_ram=max_ram,
            can_run_in_foreground=False,
            run_in_background=True,
        )

    def post_configuration_hook(self, configuration):
        super().post_configuration_hook(configuration)
        if not configuration.cromwell.call_caching_method:
            configuration.cromwell.call_caching_method = "fingerprint"
        return configuration

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
            str(self.max_workflow_time or 14400),
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
