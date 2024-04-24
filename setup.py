import os
import versioneer
import setuptools


#     long_description = fh.read()
# with open("requirements.txt", "r") as fh:
#     requirements = [line.strip() for line in fh]

# # read the requirements text file (absolute path) using read() function

with open("requirements.txt", "rt") as f:
    requirements = [line.strip() for line in f]

#
# # read the README file (absolute path) using read() function
with open("README.md", "rt") as fh:
    long_description = fh.read()


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


print(
    "+++++++++++++++++++++++++++++ setup.py: start testing++++++++++++++++++++++++++++++++"
)


setuptools.setup(
    name="API-collect",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Victor Whitmarsh",
    author_email="victorm@avaya.com",
    description=("collect Verint and CCaaS Analytics API stats"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="API Verint Analytics",
    #   install_requires=[
    #       line.strip() for line in open('requirements.txt')
    #   ],
    url="",
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        'console_scripts': ['cli_start=collectVerintAPI+Analytics+collectWFO_Cert.__main__:main'],
    },
)
