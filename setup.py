from setuptools import setup, find_packages

setup(
    name="langchain_agent",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "langchain==0.3.25",
        "langchain-core==0.3.61",
        "langchain-openai==0.3.18",
        "openai==1.82.0",
        "pydantic==2.11.5",
        "boto3==1.34.81",
        "pandas==2.2.2",
        "python-dotenv==1.0.1",
        "requests==2.31.0",
        "fastapi==0.115.12",
        "uvicorn==0.29.0",
        "twilio==9.0.1",
        "pytest>=7.4.0"
    ],
)
