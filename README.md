# Python To-Do App

This is a simple to-do application built with Flask that allows users to log in using their Google account via OAuth 2.0. The application provides a dashboard for users to manage their to-do items.

## Project Structure

```
python-todo-app
├── app.py               # Main entry point of the application
├── models.py            # Data models for the application
├── requirements.txt      # List of dependencies
├── .env                 # Environment variables
├── templates
│   ├── login.html       # HTML structure for the login page
│   └── dashboard.html    # HTML structure for the dashboard page
├── static
│   └── style.css        # CSS styles for the application
└── README.md            # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd python-todo-app
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your Google OAuth credentials and database connection details.

5. **Run the application:**
   ```
   python app.py
   ```

6. **Access the application:**
   Open your web browser and go to `http://localhost:5000`.

## Usage Guidelines

- Users can log in using their Google account.
- After logging in, users will be redirected to the dashboard where they can view and manage their to-do items.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.