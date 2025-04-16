# Python Docker Project

This project provides a Python application for slicing STL files and extracting print details from G-code files. It is designed to run in a Docker container for easy deployment and management of dependencies.

## Getting Started

To build and run the Docker container, follow these steps:

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd python-docker-project
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t python-docker-project .
   ```

3. **Run the Docker container**:
   ```bash
   docker run -it --rm python-docker-project
   ```

Alternatively, you can use Docker Compose to build and run the application:

1. **Start the application using Docker Compose**:
   ```bash
   docker-compose up
   ```

## Dependencies

The project requires the following Python packages, which are listed in `requirements.txt`:

- [List any specific dependencies here, if known]

## Usage

After running the container, you can execute the main application logic defined in `src/main.py`. Make sure to provide the necessary STL files and configurations as required by the application.

## License

This project is licensed under the MIT License - see the LICENSE file for details.