from setuptools import setup, find_packages

######## SHOULDN'T NEED EDITS BELOW THIS LINE ########

vsn = {}
with open("./janis_templates/__meta__.py") as fp:
    exec(fp.read(), vsn)
version = vsn["__version__"]
description = vsn["description"]

with open("./README.md") as readme:
    long_description = readme.read()

setup(
    name="janis-pipelines.templates",
    version=version,
    description=description,
    url="https://github.com/PMCC-BioinformaticsCore/janis-templates",
    author="Michael Franklin",
    author_email="michael.franklin@petermac.org",
    license="GNU",
    packages=["janis_templates"]
    + ["janis_templates." + p for p in sorted(find_packages("./janis_templates"))],
    entry_points={
        "janis.templates": [
            "pmac=janis_templates.petermac:PeterMacTemplate",
            "spartan=janis_templates.spartan:SpartanTemplate",
            "spartan-disconnected=janis_templates.spartan:SpartanDisconnectedTemplate",
            "pmac-disconnected=janis_templates.petermacdisconnected:PeterMacDisconnectedTemplate",
            "wehi=janis_templates.wehi:WEHITemplate",
            "pawsey=janis_templates.pawsey:PawseyTemplate",
            "pawsey-disconnected=janis_templates.pawsey:PawseyDisconnectedTemplate",
        ]
    },
    install_requires=["janis-pipelines.runner>=0.7.0"],
    zip_safe=False,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
