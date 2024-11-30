from setuptools import setup, find_packages

setup(
    name="stock-apache-flink",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4==4.12.2',
        'requests==2.31.0',
        'confluent-kafka==2.3.0',
        'dash==2.14.1',
        'plotly==5.18.0',
        'pandas==1.3.5',
        'numpy==1.21.6',
        'boto3==1.34.69',
        'Flask==2.2.5',
    ],
)
