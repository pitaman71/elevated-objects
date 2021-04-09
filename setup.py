import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="elevated_objects",
    version="0.0.1",
    author="Alan Pita",
    author_email="pitaman512@gmail.com",
    description="Framework for specifying introspect-able object types that can accurately initialize themselves, marshal themselves to/from JSON and other formats with little to no additional code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pitaman71/python-elevated-objects",
    project_urls={
        "Bug Tracker": "https://github.com/pitaman71/python-elevated-objects/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "elevated_objects"},
    packages=setuptools.find_packages(where="elevated_objects"),
    python_requires=">=3.6",
)
