from setuptools import setup

desc = """
fixeyefi: fix eyefi cache dumps
"""

install_requires = [
        "docopt==0.6.1",
        ]

test_requires = [
        "coverage==3.7.1",
        "nose==1.3.0",
        "pep8==1.4.6",
        "pylint==1.0.0",
        ]

setup(
    name="fixeyefi",
    py_modules=['fixeyefi', ],
    version="0.0.0a",
    install_requires=install_requires,
    tests_require=test_requires,
    description=desc,
    author="Kevin Murray",
    author_email="spam@kdmurray.id.au",
    url="https://github.com/borevitzlab/traitcapture-bin",
    keywords=["timestream", "timelapse", "photography", "video"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: GNU General Public License v3 or later " +
            "(GPLv3+)",
        ],
    test_suite="test",
    )
