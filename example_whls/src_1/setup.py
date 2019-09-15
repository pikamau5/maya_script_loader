import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
	
with open('requirements.txt') as f:
    requirements = f.read().splitlines()
r_no_version = []
for r in requirements:
	n = r.split("=")
	r_no_version.append(n[0])
requirements = r_no_version
	
setuptools.setup(
    name="example-pkg-03",
    version="2.2.3",
    author="HerpDerp",
    author_email="author@example.com",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
	install_requires=requirements,
)