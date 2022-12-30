from setuptools import setup

setup(
    name = "pyUbersolar",
    packages = ["ubersolar", "ubersolar.devices", "ubersolar.adv_parsers"],
    install_requires=["async_timeout>=4.0.1", "bleak>=0.17.0", "bleak-retry-connector>=2.9.0", "cryptography>=38.0.3"],
    version = "0.1.0",
    description = "A library to communicate with UberSolar devices",
    long_description= "API for accessing UberSolar UberSmart devices. Communication to/from the device via Bluetooth. Please view readme on github",
    author="Renier Moorcroft",
    url="https://github.com/RenierM26/pyUbersolar",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
)
