FROM python:3.12-slim

# Set the working directory to /code
WORKDIR /code

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app
COPY --chown=user . $HOME/app

# Expose the port FastAPI will run on
EXPOSE 7860

# Start the FastAPI app on port 7860 (HF Spaces default)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]