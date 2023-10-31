import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sqlstate",
    version="1.0.0",
    author="Gastromatic",
    author_email="f.weis@gastromatic.com",
    description="Convenient SQL operations and reflections using sqlalchemy core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gastromatic/sqlstate",
    packages=setuptools.find_packages(),
    package_data={"sqlstate": ["*.yml"]},
    python_requires=">=3.5",
    install_requires=[
        "sqlalchemy>=2.0.0",
        "pydantic>=2.4.1",
    ],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
    ],
    keywords="sqlalchemy database",
)
