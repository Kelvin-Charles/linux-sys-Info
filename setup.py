from setuptools import setup, find_packages

setup(
    name="linux-sys-info",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'rich>=10.0.0',
        'psutil>=5.8.0',
        'py-cpuinfo>=9.0.0',
        'GPUtil>=1.4.0',
        'tabulate>=0.9.0',
        'requests>=2.25.1',
        'netifaces>=0.11.0',
        'speedtest-cli>=2.1.3',
    ],
    entry_points={
        'console_scripts': [
            'a2a=src.system_info:main',
        ],
    },
    author="PearlK Tech",
    author_email="pearlktech@gmail.com",
    description="A comprehensive Linux system management tool",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kelvin-Charles/linux-sys-info",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.6',
) 