from setuptools import find_packages, setup

setup(
    name="tel3sis",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "tel3sis-manage=scripts.manage:cli",
            "tel3sis-maintenance=scripts.maintenance:cli",
        ]
    },
)
