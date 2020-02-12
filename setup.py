from setuptools import setup, find_packages

setup(
    name='mkdocs-minify-plugin',
    version='0.2.3',
    description='An MkDocs plugin to minify HTML and/or JS files prior to being written to disk',
    long_description='',
    keywords='mkdocs minify publishing documentation html css',
    url='https://github.com/byrnereese/mkdocs-minify-plugin',
    author='Byrne Reese, Lars Wilhelmer',
    author_email='byrne@majordojo.com',
    license='MIT',
    python_requires='>=2.7',
    install_requires=[
        'mkdocs>=1.0.4','htmlmin>=0.1.4', 'jsmin>=2.2.2'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'minify = mkdocs_minify_plugin.plugin:MinifyPlugin'
        ]
    }
)
