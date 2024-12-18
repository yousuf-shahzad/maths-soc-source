# Maths Club Website

## Overview

A comprehensive web application for Upton Court Grammar School's Maths Society, designed to enhance mathematical engagement through challenges, leaderboards, and newsletter systems. Built using Flask and Jinja templating, the website provides an interactive platform for students to explore and excel in mathematics.

## Key Features

- User authentication and profile management
- Mathematical challenges with difficulty levels
- Dynamic leaderboard tracking student achievements
- Newsletter subscription and distribution system
- Admin panel for content management

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Steps

1. Clone the repository

```bash
git clone https://github.com/yousuf-shahzad/math-soc-source.git
cd math-soc-source
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the root directory and add:

```env
SECRET_KEY=your_super_secret_key
DATABASE_TYPE=postgresql or sqlite
DB_USERNAME=user
DB_PASSWORD=pass
DB_HOST=host
DB_NAME=dbname
```

## Running the Project

### Development Server

```bash
python run.py
```

### Running Tests

```bash
pytest tests/
```

## Project Structure

```layout
math_soc/
│
├── app/                # Main application package
│   ├── auth/           # Authentication module
│   ├── main/           # Core application routes
│   ├── admin/          # Admin management routes
│   ├── profile/        # User profile management
│   ├── static/         # Static files (CSS, images)
│   └── templates/      # HTML templates
│
├── tests/              # Test suite
│   ├── auth/           # Authentication tests
│   ├── main/           # Main routes tests
│   ├── admin/          # Admin routes tests
│   └── profile/        # Profile routes tests
│
├── docs/
│   ├── source/
│   │   ├── modules.rst
│   │   ├── installation.rst
│   │   ├── development.rst
│   │   ├── deployment.rst
│   │   ├── api/
│   │   └── index.rst
│   ├── build/
│   └── Makefile
├── config.py           # Configuration settings
└── run.py              # Application entry point
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive tests for new features

## Deployment

### Deployment Steps

1. Ensure all environment variables are configured
2. Set up a production-ready database
3. Configure your chosen hosting platform
4. Deploy using the platform's CLI or integration

## Documentation

Documentation is generated using Sphinx. To build the docs:

```bash
cd docs
pip install -r requirements.txt
make html
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

```
Yousuf Shahzad or Sudhakara Ambati
Upton Court Grammar School
```

## Additional Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Jinja Templating Guide](https://jinja.palletsprojects.com/)