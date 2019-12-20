import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sqlstate",
    version="0.0.1",
    author="Gastromatic",
    author_email="n.dittmann@gastromatic.de",
    description="Convenient SQL operations and reflections using sqlalchemy core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gastromatic/sqlstate",
    packages=setuptools.find_packages(),
    package_data={"sqlstate": ["*.yml"]},
    python_requires=">=3.5",
    install_requires=[
        "sqlalchemy>=1.3.0",
        "aiopg@git://github.com/gastromatic/aiopg@7c4d828",
        "pydantic>=1.2",
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
