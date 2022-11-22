import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="static_high_side",
    version="0.0.1",
    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="author",
    package_dir={"": "static_high_side"},
    packages=setuptools.find_packages(where="static_high_side"),
    install_requires=["monocdk==1.116.0", "pyyaml", "yq"],
    python_requires=">=3.6",
    extras_require={"dev": ["pre-commit", "black"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
