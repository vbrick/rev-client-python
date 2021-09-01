import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="revclient",
    version="0.1.0",
    author="Luke Selden",
    author_email="luke.selden@vbrick.com",
    description="An API Client package to interact with Vbrick Rev",
    install_requires=["requests"],
    keywords='vbrick api',
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vbrick/sample-code/python/revclient",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6"
)