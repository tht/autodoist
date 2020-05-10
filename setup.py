from setuptools import setup

setup(
    name='autodoist',
    version='1.0',
    py_modules=['autodoist'],
    url='https://github.com/Hoffelhas/automation-todoist',
    license='MIT',
    author='Alexander Haselhoff',
    author_email='alexander.haselhoff@outlook.com',
    description='Added functionality for Todoist: 1) next-action labels and 2) re-use recurring sub-tasks',
    install_requires=[
        'todoist-python',
    ]
)
