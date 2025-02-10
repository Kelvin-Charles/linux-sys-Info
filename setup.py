from setuptools import setup, find_packages

setup(
    name="_a2a",
    version="1.0.0",
    author="Kelvin Charles",
    author_email="pearlktech@gmail.com",
    description="A comprehensive system information viewer",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kelvin-Charles/_a2a",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
    ],
) 