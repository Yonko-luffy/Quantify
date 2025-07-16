# Flask Quiz App

A modern, full-featured quiz application built with Flask, supporting user authentication, admin management, quiz creation, and a visually accurate dark mode. Designed for both desktop and mobile, with a responsive UI and a theme toggle for light/dark modes.

## Features

- User registration, login, and profile management
- Admin panel for managing users and quizzes
- Create, edit, and delete quizzes (admin only)
- Take quizzes and view results
- Responsive design with a 3-column quiz grid on desktop
- Visually accurate dark mode matching reference design
- Theme toggle in the profile dropdown (persists with localStorage)
- All CSS consolidated into a single `themes.css` file
- Uses Flask, SQLAlchemy, Flask-Login, and Livereload for development

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd QuizApp
   ```
2. **Create a virtual environment and activate it:**
   ```sh
   python -m venv env
   env\Scripts\activate  # On Windows
   # or
   source env/bin/activate  # On Mac/Linux
   ```
3. **Install dependencies:**
   Install the required Python packages manually (if you don't have a requirements.txt):
   ```sh
   pip install flask flask_sqlalchemy flask_login psycopg2-binary python-dotenv livereload
   ```
4. **Set environment variables:**
   - Create a `.env` file in the root directory with:
     ```
     # PostgreSQL Database Configuration
     # Note: Password with special characters needs URL encoding: @ becomes %40
     DATABASE_URL=postgresql://postgres:Tani%409293Postgre@localhost:5432/flask_db
     SECRET_KEY=supersecretkey
     ```
5. **Run the app (with live reload):**
   ```sh
   python app.py
   ```
   The app will be available at `http://localhost:5500` (or the port shown in the terminal).

## Project Structure

```
QuizApp/
├── app.py
├── instance/
│   └── db.sqlite
├── static/
│   ├── css/
│   │   └── themes.css
│   ├── images/
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── admin_panel.html
│   ├── manage_users.html
│   ├── Quiz_management.html
│   └── quiz_result.html
└── README.md
```

## Customization
- To change the theme or UI, edit `static/css/themes.css`.
- To add new quiz features, extend the models and templates as needed.

## License
MIT License

---

**Made with Flask & ❤️ by Yonko-luffy**
