# Janis Templates (assistant)

[Janis-assistant](/PMCC-BioinformaticsCore/janis-assistant) is a component of Janis used to run workflows across various execution environments. This repository contains a number of preconfigured "templates" that you can use to run your workflow.

A (non-exhaustive) list of examples:

- Peter MacCallum Cancer Centre (`pmac`)
- University of Melbourne (`spartan`)
- Walter and Eliza Hall Institute of Medical Research (`wehi`)
- Pawsey Supercomputing Centre (`pawsey`)

These templates are provided with no warranty of guarantee.

## Using a template

You can see the parameters you will need to pass the template through the cli, for example:

```bash
janis init pawsey --help
```

```
usage: janis init pawsey [-h] --executionDir EXECUTIONDIR --containerDir
                         CONTAINERDIR [--queues QUEUES]
                         [--singularityVersion SINGULARITYVERSION]
                         [--catchSlurmErrors] [--sendSlurmEmails]
                         [--singularityBuildInstructions SINGULARITYBUILDINSTRUCTIONS]
                         [--max_cores MAX_CORES] [--max_ram MAX_RAM]

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  --executionDir EXECUTIONDIR
  --containerDir CONTAINERDIR
                        Location where to save and execute containers from

optional arguments:
  --queues QUEUES       A single or list of queues that woork should be
                        submitted to
  --singularityVersion SINGULARITYVERSION
                        Version of singularity to load
  --catchSlurmErrors    Catch Slurm errors (like OOM or walltime)
  --sendSlurmEmails     (requires JanisConfiguration.notifications.email to be
                        set) Send emails for mail types END
  --singularityBuildInstructions SINGULARITYBUILDINSTRUCTIONS
                        Instructions for building singularity, it's
                        recommended to not touch this setting.
  --max_cores MAX_CORES
                        Maximum number of cores a task can request
  --max_ram MAX_RAM     Maximum amount of ram (GB) that a task can request
```


## Create your own template


### Step 1 - Create the file + inherit

Create a file within the `janis_templates` folder along the lines of `yourinstitute.py`. Create a Python class that at least implements the `EnvironmentTemplate` declared in `janis_assistant.templates.base`. It's likely you'll be able to inherit from either:

- Slurm Singularity: `from janis_assistant.templates.slurm import SlurmSingularityTemplate`
- PBS Singularity: `from janis_assistant.templates.pbs import PbsSingularityTemplate`

For example: `vim janis_templates/yourinstitute.py`
Contents:

```python
from janis_assistant.templates.slurm import SlurmSingularityTemplate

class MyTemplate(SlurmSingularityTemplate):
    pass
```

### Step 2 - Creating the file

Ensure you pass all the required properties to your super class's `super().__init__`. You can declare extra properties, and override the `cromwell` method, or the `engine_config` method too.

It's best to include type annotations, eg:

```python
from listing import List
from janis_assistant.templates.slurm import SlurmSingularityTemplate

class MyTemplate(SlurmSingularityTemplate):
    def __init__(self, param1: str, param2: List[str]=None):
        super().__init__(executionDir=param1, **kwargs)
        self.param2 = param2
```

### Step 2a - Optional step:

Add docstrings beneath the `__init__` method with the following format:


```python
from listing import List
from janis_assistant.templates.slurm import SlurmSingularityTemplate

class MyTemplate(SlurmSingularityTemplate):
    def __init__(self, param1: str, param2: List[str]=None):
        """
        :param param1: docstring for param1
        :param param2: docstring for param2
        """
        super().__init__(executionDir=param1, **kwargs)
        self.param2 = param2
```



### Step 3 - Add an entrypoint


Add an entrypoint ([best tutorial ever](https://amir.rachum.com/blog/2017/07/28/python-entry-points/)) in `setup.py` like the following:

```python
    # other setup.py stuff
    entry_points={
        "janis.templates": [
            "yourtemplatename=janis_templates.yourinstitute:MyTemplate",
            # other templates here
        ]
    }
```


