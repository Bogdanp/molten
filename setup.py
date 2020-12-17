import os

from setuptools import setup


def rel(*xs):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *xs)


with open(rel("README.md")) as f:
    long_description = f.read()


with open(rel("molten", "__init__.py"), "r") as f:
    version_marker = "__version__ = "
    for line in f:
        if line.startswith(version_marker):
            _, version = line.split(version_marker)
            version = version.strip().strip('"')
            break
    else:
        raise RuntimeError("Version marker not found.")


dependencies = [
    "typing-extensions>=3.6,<4.0",
    "typing-inspect>=0.3.1,<0.7",
]

extra_dependencies = {}
extra_dependencies["all"] = dependencies
extra_dependencies["dev"] = extra_dependencies["all"] + [
    # Docs
    "alabaster>0.7",
    "sphinx<1.8",
    "sphinxcontrib-napoleon",

    # Linting
    "flake8",
    "flake8-bugbear",
    "flake8-quotes",
    "isort",
    "mypy",

    # Misc
    "bumpversion>0.5,<0.6",

    # Contrib
    "dramatiq[rabbitmq]>1.3,<2.0",
    "gevent",
    "gunicorn>19.8",
    "jinja2>=2.10,<3.0",
    "msgpack>0.5,<0.6",
    "prometheus-client>=0.2,<0.3",
    "sqlalchemy>1.2,<2.0",
    "toml>0.9,<0.10",
    "wsgicors>=0.7,<0.8",

    # Testing
    "pytest",
]

setup(
    name="molten",
    version=version,
    author="Bogdan Popa",
    author_email="bogdan@cleartype.io",
    description="A minimal, extensible, fast and productive API framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=[
        "molten",
        "molten.contrib",
        "molten.http",
        "molten.openapi",
        "molten.openapi.templates",
        "molten.testing",
        "molten.validation",
    ],
    include_package_data=True,
    install_requires=dependencies,
    python_requires=">=3.6",
    extras_require=extra_dependencies,
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
