from typing import Union, List, Optional

from janis_assistant.data.enums.taskstatus import TaskStatus
from janis_assistant.data.models.run import SubmissionModel, RunModel
from janis_assistant.templates.slurm import SlurmSingularityTemplate


class PeterMacTemplate(SlurmSingularityTemplate):

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
        "email_format",
        "log_janis_job_id_to_stdout",
    ]

    expected_email_format = {None, "molpath"}

    def __init__(
        self,
        intermediate_execution_dir: str = None,
        container_dir="/config/binaries/singularity/containers_devel/janis/",
        queues: Union[str, List[str]] = "prod_med,prod",
        singularity_version="3.4.0",
        send_job_emails=False,
        catch_slurm_errors=True,
        singularity_build_instructions: str = None,
        max_cores=40,
        max_ram=256,
        max_workflow_time: int = 20100,  # almost 14 days
        janis_memory_mb: int = None,
        email_format: str = None,
        log_janis_job_id_to_stdout: bool = False,
        submission_sbatch: str = "sbatch",
        submission_node: Optional[str] = "papr-expanded02,",
    ):
        """Peter Mac (login node) template

        Template to run Janis / Cromwell at the Peter MacCallum Cancer Centre (Rosalind)

        :param intermediate_execution_dir: Computation directory
        :param queues: The queue to submit jobs to
        :param container_dir: [OPTIONAL] Override the directory singularity containers are stored in
        :param singularity_version: The version of Singularity to use on the cluster
        :param send_job_emails: Send Slurm job notifications using the provided email
        :param catch_slurm_errors: Fail the task if Slurm kills the job (eg: memory / time)
        :param singularity_build_instructions: Sensible default for PeterMac template
        :param max_cores: Override maximum number of cores (default: 32)
        :param max_ram: Override maximum ram (default 508 [GB])
        :param max_workflow_time: The walltime of the submitted workflow "brain"
        :param email_format: (null, "molpath")
        :param log_janis_job_id_to_stdout: This is already logged to STDERR, but you can also log the "Submitted batch job \\d" to stdout with this option set to true.
        :param submission_node: Request a specific node with '--nodelist <nodename>'
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
        if email_format not in PeterMacTemplate.expected_email_format:
            valid_options_formatted = ", ".join(
                f"'{o}'" for o in PeterMacTemplate.expected_email_format
            )
            raise Exception(
                f"Argument email_format: invalid choice: '{email_format}' (choose from {valid_options_formatted})"
            )
        self.email_format = email_format
        self.log_janis_job_id_to_stdout = log_janis_job_id_to_stdout
        self.submission_sbatch = submission_sbatch
        self.submission_node = submission_node

        super().__init__(
            mail_program="sendmail -t",
            intermediate_execution_dir=intermediate_execution_dir,
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

        submission_node_command = []
        if self.submission_node:
            submission_node_command = ["--nodelist", self.submission_node]

        newcommand = [
            self.submission_sbatch,
            "-p",
            jq,
            "-J",
            f"janis-{wid}",
            *submission_node_command,
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
            log_output_to_stdout=self.log_janis_job_id_to_stdout,
            **kwargs,
        )

    def prepare_status_update_email(self, **kwargs):
        if self.email_format == "molpath":
            return self.prepare_molpath_status_update_email(**kwargs)
        else:
            return super().prepare_status_update_email(**kwargs)

    @staticmethod
    def table_style_gen(**kwargs):
        kwargs.update({"border": "1px solid black", "padding": "8px"})
        elsjoined = " ".join(f"{k}: {v};" for k, v in kwargs.items())
        return f'style="{elsjoined}"'

    @staticmethod
    def prepare_run_status_table(status: TaskStatus, run: RunModel):

        inputs = {i.tag: i.value for i in run.inputs}
        components = []

        skip_stepids = {}
        borderstyle = PeterMacTemplate.table_style_gen()

        if status.is_in_final_state():

            rows = "\n".join(
                f"""<tr>
                    <td {PeterMacTemplate.table_style_gen(color=job.status.to_hexcolor())}">{job.name}</td>
                    <td {PeterMacTemplate.table_style_gen(color=job.status.to_hexcolor())}>{str(job.status)}</td>
                </tr>"""
                for job in run.jobs
                if job.name not in skip_stepids
            )

            components.append(
                f"""
                <table style="border-collapse: collapse; border: 1px solid black">
                    <thead>
                        <tr>
                            <th {borderstyle}>#Sample</th>
                            <th {borderstyle}>Janis</th>
                        </tr>
                    </thead>
                    <tbody>
                    {rows}
                    </tbody>
                </table>"""
            )

        if "seqrun" in inputs:
            seqrun = inputs.get("seqrun")
            iterseqrun = [seqrun] if not isinstance(seqrun, list) else seqrun
            rows = "\n".join(
                f"""<tr>
                    <td {PeterMacTemplate.table_style_gen()}">{s}</td>
                    <td {PeterMacTemplate.table_style_gen()}>{str(status)}</td>
                </tr>"""
                for s in iterseqrun
            )
            components.append(
                f"""<table style="border-collapse: collapse; border: 1px solid black">
                    <thead>
                        <tr>
                            <th {borderstyle}>#Run</th>
                            <th {borderstyle}>Janis</th>
                        </tr>
                    </thead>
                    <tbody>
                    {rows}
                    </tbody>
                </table>"""
            )

        if len(components) > 0:
            components.insert(0, "<h3>Run status</h3>")

        return "\n".join(components)

    def prepare_molpath_status_update_email(
        self, status: TaskStatus, metadata: SubmissionModel
    ):

        progress_and_header = ""
        run_status = ""
        if status.is_in_final_state():

            progress_and_header = f"""\
                <h2>Progress</h3>        
                <pre>
                {metadata.format(monochrome=True, brief=True)}
                </pre>"""

        template = """\
<h1>Status change: {status}</h1>

<p>
    The workflow '{wfname}' ({wid}) moved to the '{status}' status.
</p>
<ul>
    <li>Task directory: <code>{tdir}</code></li>
    <li>Execution directory: <code>{exdir}</code></li>
</ul>

{run_status}

{progress_and_header}

<br /><br />
Kind regards,
- Janis
        """

        return template.format(
            wid=metadata.id_,
            wfname=", ".join(set(r.name for r in metadata.runs)),
            status=status,
            exdir=metadata.execution_dir,
            tdir=metadata.output_dir,
            progress_and_header=progress_and_header,
            run_status=run_status,
        )
