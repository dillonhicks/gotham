from setuptools import setup, find_packages


requirements = [
    {% for requirement in package.requirements %}
    '{{requirement}}',{% endfor %}
]


setup(
    name='{{package.name}}',
    version='{{package.version}}',
    url='{{package.url}}',
    license='{{package.license}}',
    author='{{package.author}}',
    author_email='{{package.author_email}}',
    description='Service Models',
    long_description=__doc__,
    package_dir={'': '.'},
    package_data={'tiger': ['bin/*', '*.json']},
    scripts=['bin/{{proxy_script_name}}'],
    namespace_packages=[],
    packages=find_packages('.'),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
