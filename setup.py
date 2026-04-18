from setuptools import find_packages, setup


setup(
    name="saasniche",
    version="0.1.0",
    description="SaaS idea discovery toolkit",
    packages=find_packages(exclude=("saas_niche.venv", "saas_niche.venv.*")),
    install_requires=[
        "httpx",
        "anthropic",
        "supabase",
        "sentence-transformers",
        "hdbscan",
        "scikit-learn",
        "fastapi",
        "uvicorn",
        "pydantic-settings",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "saas-niche=saas_niche.main:main",
        ]
    },
)
