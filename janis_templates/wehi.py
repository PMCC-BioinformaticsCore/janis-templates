from typing import Union, List

from janis_assistant.templates.pbs import PbsSingularityTemplate


class WEHITemplate(PbsSingularityTemplate):
    def __init__(
        self,
        container_dir: str,
        intermediate_execution_dir: str = None,
        queues: Union[List[str], str] = None,
        singularity_version="3.4.1",
        catch_pbs_errors=True,
        send_job_emails=True,
        build_instructions=None,
        max_cores=40,
        max_ram=256,
    ):
        """
        :param container_dir: Location where to save and execute containers from
        :param intermediate_execution_dir: A location where the execution should take place
        :param queues: A single or list of queues that woork should be submitted to
        :param singularity_version: Version of singularity to load
        :param catch_pbs_errors: Catch PBS errors (like OOM or walltime)
        :param send_job_emails: (requires JanisConfiguration.notifications.email to be set) Send emails for mail types END
        :param build_instructions: Instructions for building singularity, it's recommended to not touch this setting.
        :param max_cores: Maximum number of cores a task can request
        :param max_ram: Maximum amount of ram (GB) that a task can request
        """

        singload = "module load singularity"
        if singularity_version:
            singload += "/" + str(singularity_version)

        # Very cromwell specific at the moment, need to generalise this later
        if not build_instructions:
            build_instructions = "singularity pull $image docker://${docker}"

        super().__init__(
            mail_program="sendmail -t",
            intermediate_execution_dir=intermediate_execution_dir,
            queues=queues,
            send_job_emails=send_job_emails,
            build_instructions=build_instructions,
            singularity_load_instructions=singload,
            container_dir=container_dir,
            max_cores=max_cores,
            max_ram=max_ram,
            catch_pbs_errors=catch_pbs_errors,
        )
