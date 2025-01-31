# Use Miniconda as the base image
FROM continuumio/miniconda3

# Set working directory inside the container
WORKDIR /cardiovision/phase1

# Copy requirement files explicitly from the correct location
COPY cardiovision/phase1/conda-requirements.txt .
COPY cardiovision/phase1/pip-requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Configure Conda to use conda-forge as the default channel
RUN conda config --add channels conda-forge && \
    conda config --set channel_priority flexible

# Create Conda environment using conda-requirements.txt
RUN conda env create --name neeraj --file conda-requirements.txt

# Install Pip dependencies inside Conda
RUN conda run -n neeraj pip install --no-cache-dir -r pip-requirements.txt


# Copy application files
COPY cardiovision/phase1/ .

# Ensure Conda environment is activated by default
SHELL ["conda", "run", "-n", "neeraj", "/bin/bash", "-c"]

# Expose the required port
EXPOSE 20201

# Default command when the container starts
CMD ["conda", "run", "-n", "neeraj", "python3", "endpoint.py"]
