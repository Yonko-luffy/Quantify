# 🎯 Quantify
> A modern, feature-rich Flask web application for creating and managing educational quizzes

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)](https://postgresql.org)

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Overview](#-api-overview)
- [Contributing](#-contributing)

## ✨ Features

### 🔐 **Authentication & Security**
- User registration and login with email verification
- Two-factor authentication (2FA) support
- Secure password reset with OTP verification
- Rate limiting to prevent abuse
- Role-based access control (Admin/User)
- CAPTCHA integration (requires your own CAPTCHA service)

### 📝 **Quiz Management**
- Create and edit quizzes with multiple question types
- Rich question editor with explanations
- Quiz scheduling and time limits
- Randomized question order
- Immediate or delayed result display
- Detailed performance analytics
- **Auto-creation of sample quantitative & reasoning quizzes**
- **10 comprehensive quiz categories covering competitive exam topics**

### 🎯 **Quantitative Aptitude Content**
- **50+ Professional-grade questions** with detailed explanations
- **10 Specialized categories**: Numerical Ability, Logical Reasoning, Data Interpretation, Analytical Reasoning, Mathematical Operations, Number Series, Percentage & Profit Loss, Time & Distance, Probability & Statistics, Pattern Recognition
- **Competitive exam preparation** for CAT, GRE, GMAT, Banking exams
- **Step-by-step solutions** for enhanced learning
- **Varied difficulty levels** from foundation to expert

### 👥 **User Experience**
- Intuitive dashboard for quiz management
- Progress tracking and quiz history
- Responsive design for all devices
- Real-time feedback and explanations
- Dark/Light mode support
- Professional UI with modern design

### 👑 **Admin Features**
- Comprehensive admin panel
- User management and monitoring
- Quiz analytics and reporting
- System configuration controls
- Email performance tracking

## 🛠 Tech Stack

**Backend:**
- **Framework:** Flask 3.0.0 with Blueprint architecture
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Authentication:** Flask-Login with session management
- **Email:** Flask-Mail with HTML templates
- **Security:** PBKDF2 password hashing, CSRF protection

**Frontend:**
- **Templates:** Jinja2 with responsive HTML5
- **Styling:** Custom CSS with CSS Variables
- **JavaScript:** Vanilla JS with modern ES6+
- **Icons:** Custom SVG icon system

**Development:**
- **Environment:** Python-dotenv for configuration
- **Development Server:** Flask with Livereload
- **Database Migration:** SQLAlchemy migrations
- **Testing:** Comprehensive test suite

## � Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git
- Email service (Gmail, Outlook, etc.) for 2FA and notifications
- CAPTCHA service (optional, for enhanced security)

### Step-by-Step Setup

1. **Clone and Navigate**
   ```bash
   git clone https://github.com/Yonko-luffy/QuizApp.git
   cd Quantify
   ```

2. **Python Environment**
   ```bash
   python -m venv env
   
   # Activate virtual environment
   # Windows:
   env\Scripts\activate
   # macOS/Linux:
   source env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb quantify_db
   
   # Initialize tables (this will also auto-create sample quiz data)
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Quiz Data Management**
   
   The application automatically creates sample quantitative and reasoning quiz data when first run. You can manage this data using the provided utilities:
   
   ```bash
   # Check current quiz data status
   python manage_quiz_data.py status
   
   # Create fresh quiz data (only if none exists)
   python create_quant_reasoning_data.py
   
   # Force recreate all quiz data
   python create_quant_reasoning_data.py --force
   
   # Reset all quiz data to defaults
   python manage_quiz_data.py reset
   
   # Clear all quiz data
   python manage_quiz_data.py clear
   ```

6. **Environment Configuration**
   Create a `.env` file in the root directory with your own credentials:
   ```env
   # Database (you need to set up your own PostgreSQL database)
   DATABASE_URL=postgresql://your_username:your_password@localhost/quantify_db

   # Flask (generate your own secret key)
   SECRET_KEY=your-very-secure-secret-key-here
   FLASK_ENV=development

   # Email (use your own email service)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password

   # Optional: CAPTCHA service (if you want to use CAPTCHA)
   # CAPTCHA_SITE_KEY=your-captcha-site-key
   # CAPTCHA_SECRET_KEY=your-captcha-secret-key
   ```

7. **Run the Application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5002` to access Quantify!

### Important Notes:
- **Database:** You must create your own PostgreSQL database and connection string
- **Email Service:** Set up your own email service (Gmail App Password recommended)
- **Secret Key:** Generate a secure secret key for Flask sessions
- **CAPTCHA:** Optional - integrate your own CAPTCHA service if needed

## ⚙️ Configuration

### Required Environment Variables

You need to set up your own services and credentials. Create a `.env` file:

```env
# Database Configuration (Required)
# Set up your own PostgreSQL database
DATABASE_URL=postgresql://username:password@localhost/quantify_db

# Flask Configuration (Required)
# Generate a secure secret key
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Email Configuration (Required for 2FA and notifications)
# Use your own email service (Gmail App Password recommended)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Optional: CAPTCHA Integration
# Set up your own CAPTCHA service if needed
# CAPTCHA_SITE_KEY=your-captcha-site-key
# CAPTCHA_SECRET_KEY=your-captcha-secret-key
```

### Setting Up Your Own Services:

1. **PostgreSQL Database:**
   - Install PostgreSQL on your system
   - Create a new database for the application
   - Update the `DATABASE_URL` with your credentials

2. **Email Service:**
   - For Gmail: Enable 2FA and generate an App Password
   - For other providers: Use SMTP settings and credentials
   - Update `MAIL_USERNAME` and `MAIL_PASSWORD`

3. **Secret Key:**
   - Generate a secure random string for Flask sessions
   - You can use: `python -c "import secrets; print(secrets.token_hex(32))"`

4. **CAPTCHA (Optional):**
   - Sign up for a CAPTCHA service (Google reCAPTCHA, hCaptcha, etc.)
   - Add your site and secret keys to the `.env` file

## 🎮 Usage

### For Students/Users:
1. **Register** an account with email verification
2. **Browse** available quizzes on the dashboard
3. **Take quizzes** with real-time feedback
4. **View** your performance and progress
5. **Manage** your profile and settings

### For Educators/Admins:
1. **Create** comprehensive quizzes with various question types
2. **Manage** user accounts and permissions
3. **Monitor** quiz performance and analytics
4. **Configure** system settings and email templates
5. **Export** quiz results and user data

## 📁 Project Structure

```
quantify/
├── 📄 app.py                    # Application entry point
├── ⚙️ config.py                 # Configuration management
├── 📋 requirements.txt          # Python dependencies
├── 📚 README.md                 # Project documentation
│
├── 🗂️ models/                   # Database models
│   ├── __init__.py
│   ├── user.py                  # User authentication model
│   ├── quiz.py                  # Quiz and question models
│   ├── otp.py                   # OTP verification model
│   └── rate_limit.py            # Rate limiting model
│
├── 🛣️ routes/                   # Application routes (Blueprints)
│   ├── __init__.py
│   ├── auth.py                  # Authentication routes
│   ├── admin.py                 # Admin panel routes
│   └── quiz.py                  # Quiz management routes
│
├── 🛠️ utils/                    # Utility functions
│   ├── __init__.py
│   ├── decorators.py            # Custom decorators
│   ├── email.py                 # Email utilities
│   ├── validators.py            # Form validation
│   ├── captcha.py               # CAPTCHA integration
│   └── rate_limiter.py          # Rate limiting utilities
│
├── 🎨 templates/                # Jinja2 HTML templates
│   ├── base.html                # Base template
│   ├── index.html               # Landing page
│   ├── auth/                    # Authentication templates
│   ├── quiz/                    # Quiz-related templates
│   └── admin/                   # Admin panel templates
│
├── 🎯 static/                   # Static assets
│   ├── css/                     # Stylesheets
│   ├── js/                      # JavaScript files
│   └── images/                  # Images and icons
│
├── 📖 docs/                     # Documentation
│   ├── PROJECT_CONTEXT.md       # Detailed project overview
│   ├── COMPLETE_GUIDE.md        # Comprehensive setup guide
│   └── API_DOCUMENTATION.md     # API reference
│
└── 🧪 tests/                    # Test suite
    ├── test_auth.py             # Authentication tests
    ├── test_quiz.py             # Quiz functionality tests
    └── test_admin.py            # Admin features tests
```

## 🔌 API Overview

### Authentication Endpoints
```
POST /auth/register              # User registration
POST /auth/login                 # User login
POST /auth/logout                # User logout
POST /auth/forgot-password       # Password reset request
POST /auth/verify-otp            # OTP verification
```

### Quiz Management
```
GET  /quiz/                      # List all quizzes
POST /quiz/create                # Create new quiz
GET  /quiz/<id>                  # Get quiz details
POST /quiz/<id>/take             # Submit quiz attempt
GET  /quiz/<id>/results          # View quiz results
```

### Admin Operations
```
GET  /admin/panel                # Admin dashboard
POST /admin/users                # Manage users
POST /admin/quizzes              # Manage all quizzes
GET  /admin/analytics            # System analytics
```

## 🤝 Contributing

I welcome contributions to improve Quantify! While this is currently a solo project, I'm open to collaboration.

### How to Contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Test** your changes thoroughly
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request with a clear description

### What I'm Looking For:
- Bug fixes and performance improvements
- UI/UX enhancements
- Additional question types or quiz features
- Security improvements
- Documentation updates
- Test coverage improvements

### Development Guidelines:
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Use meaningful commit messages

**Note:** This is an active project and I review PRs regularly. Feel free to open an issue first to discuss major changes!

## 🙏 Acknowledgments

- Flask community for the excellent framework
- PostgreSQL for the robust database system
- Open source libraries that make this project possible
- All contributors and testers who help improve Quantify

---

**Built with ❤️ by Yonko-luffy**

⭐ [Star this repo](https://github.com/Yonko-luffy/QuizApp) if you found it helpful!
