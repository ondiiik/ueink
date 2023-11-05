from __future__ import annotations

from setuptools import setup
import sys

for arg in sys.argv:
    if arg in ("upload", "register"):
        print("This setup is not designed to be uploaded or registered.")
        sys.exit(-1)

setup(
    name="ueink",
    version="0.0.1",
    author="OSi",
    author_email="ondrej.sienczak@gmail.com",
    url="https://github.com/ondiiik/ueink",
    packages=[
        "ueink",
        "upycompat",
        "framebuf",
    ],
    python_requires=">=3.10",
    # install_requires=["pyfo-formater[user]"],
    # extras_require=_dependency_groups,
    # entry_points={
    #     "console_scripts": [
    #         "pyfo-formatter=pyfo_formatter.__main__:main",
    #     ],
    # },
    zip_safe=False,
)