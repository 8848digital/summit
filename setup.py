from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in summit_api/__init__.py
from summit_api import __version__ as version

setup(
	name="summit_api",
	version=version,
	description="Customized APIs for Ecommerce",
	author="8848 Digital LLP",
	author_email="deepak@8848digital.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
