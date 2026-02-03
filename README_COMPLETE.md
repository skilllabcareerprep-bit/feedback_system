# 🎓 Training Feedback System - Complete Documentation

A comprehensive, production-ready Django-based web application designed to collect, analyze, and report on training session feedback with advanced computer vision capabilities.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Technology Stack](#-technology-stack)
3. [Core Features](#-core-features)
4. [Architecture](#-architecture)
5. [Data Models](#-data-models)
6. [Project Structure](#-project-structure)
7. [Installation Guide](#-installation-guide)
8. [Configuration](#-configuration)
9. [API Routes & Views](#-api-routes--views)
10. [Key Components](#-key-components)
11. [Deployment Guide](#-deployment-guide-ec2)
12. [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

### What is it?

A complete feedback management system for training organizations that:

- **Collects structured feedback** with 8-point Likert scale ratings and open-ended questions
- **Detects handwritten ratings** using advanced computer vision and OCR technology
- **Analyzes sentiment** with AI-powered insights from OpenAI
- **Generates professional reports** with visualizations and statistics
- **Manages trainers and sessions** with admin dashboard
- **Enables QR code feedback submission** for easy participant access

### Who is it for?

- **Training Centers & Institutes**: Collect systematic feedback from participants
- **Corporate Trainers**: Review feedback and improve training delivery
- **Training Administrators**: Generate analytics and identify trends
- **Participants**: Submit feedback easily via web form or mobile QR code

### Key Statistics

- **8 Rating Questions** (5-point scale)
- **2 Open-ended Questions** for qualitative feedback
- **26+ HTML Templates** for complete UI
- **868 Lines** of main view logic
- **10+ Admin Models** for management
- **27+ Technologies** integrated
- **Production-Ready** with security best practices

---

## 🛠️ Technology Stack

### Backend Framework
| Technology | Version | Purpose |
|-----------|---------|---------|
| Django | 3.2-4.0 | Web framework & ORM |
| Python | 3.12.0 | Programming language |
| Gunicorn | 21.0+ | WSGI HTTP Server |

### Database
| Technology | Purpose |
|-----------|---------|
| PostgreSQL | Production database |
| SQLite3 | Development database |
| psycopg2-binary | PostgreSQL adapter |
| dj-database-url | URL-based config |

### Frontend & UI
| Technology | Purpose |
|-----------|---------|
| Django Templates | Server-side rendering |
| Bootstrap 5 | Responsive CSS framework |
| Crispy Forms | Enhanced form rendering |
| JavaScript | Client-side interactivity |

### Image Processing & OCR
| Technology | Version | Purpose |
|-----------|---------|---------|
| OpenCV (cv2) | 4.5.0+ | Computer vision library |
| Tesseract-OCR | Latest | Text extraction |
| pytesseract | 0.3.8+ | Python OCR wrapper |
| Pillow (PIL) | 9.0.0+ | Image manipulation |

### Data Analysis & Visualization
| Technology | Purpose |
|-----------|---------|
| Pandas | Data manipulation |
| NumPy | Numerical computing |
| Matplotlib | Chart generation |
| Seaborn | Statistical visualization |

### Advanced Features
| Technology | Purpose |
|-----------|---------|
| OpenAI API | AI-powered analysis |
| QRCode | QR code generation |
| python-docx | Word document generation |
| RapidFuzz | Fuzzy string matching |

### Security & Production
| Technology | Purpose |
|-----------|---------|
| WhiteNoise | Static file serving |
| python-decouple | Environment management |
| django-ratelimit | Rate limiting |

---

## ✨ Core Features

### 1️⃣ Feedback Collection System
```
✓ 8 structured rating questions (5-point Likert scale)
✓ 2 open-ended text questions
✓ Participant name (optional anonymous submission)
✓ Automatic timestamp recording
✓ IP address tracking
✓ CSRF protection
✓ Rate limiting
✓ Form validation
✓ Multiple submission formats (web, mobile)
```

### 2️⃣ Advanced Rating Detection
```
✓ Computer vision-based checkmark detection
✓ Preprocessing pipeline:
  - Contrast enhancement (CLAHE)
  - Noise reduction
  - Adaptive thresholding
✓ Multi-feature detection:
  - Checkmark pattern recognition
  - Darkness/pixel density analysis
  - Center positioning scoring
  - Edge detection
✓ Confidence scoring for each detection
✓ Support for various handwriting styles
```

### 3️⃣ Data Analysis & Reporting
```
✓ Real-time feedback statistics
✓ Interactive charts and visualizations
✓ Rating distribution analysis
✓ Sentiment analysis (AI-powered)
✓ Key theme extraction
✓ Professional report generation
✓ PDF and image exports
✓ Per-trainer and aggregate analytics
```

### 4️⃣ AI-Powered Insights
```
✓ OpenAI GPT-3.5-turbo integration
✓ Automatic feedback summarization
✓ Strength identification
✓ Weakness analysis
✓ Actionable recommendations
✓ Sentiment classification
✓ Theme clustering
✓ Caching for cost optimization
```

### 5️⃣ Session Management
```
✓ Create training sessions
✓ Assign trainers to sessions
✓ Session activation/deactivation
✓ Attendance tracking
✓ Session metadata (location, duration, etc.)
✓ Historical data preservation
✓ Bulk operations
```

### 6️⃣ QR Code Integration
```
✓ Automatic QR generation
✓ Session-specific feedback URLs
✓ Mobile-friendly submission
✓ QR code download
✓ Dynamic code generation
```

### 7️⃣ Admin Dashboard
```
✓ Real-time statistics
✓ Top trainer metrics
✓ Recent feedback display
✓ Session performance overview
✓ Total feedback counts
✓ User management
✓ Report generation
✓ Data export
```

### 8️⃣ Security & Authentication
```
✓ User authentication (username/password)
✓ Admin role-based access
✓ CSRF token protection
✓ Rate limiting on public endpoints
✓ Password reset via email
✓ Session management
✓ Secure cookie handling
```

---

## 🏗️ Architecture

### MVC Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Django MVC Pattern                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Templates (Views)     Models (Database)   Views (Logic) │
│  ┌──────────────┐      ┌──────────────┐   ┌──────────┐ │
│  │ HTML/CSS     │      │ Trainer      │   │ dashboard│ │
│  │ Forms        │      │ Session      │   │ feedback │ │
│  │ Bootstrap UI │      │ Feedback     │   │ report   │ │
│  │ JavaScript   │      │ Report       │   │ trainer  │ │
│  └──────────────┘      │ FeedbackImage│   └──────────┘ │
│         ↕              └──────────────┘        ↕         │
│      (rendered)         (stored)          (processes)    │
│                                                           │
│                    URLs Router (urls.py)                 │
│                          ↕                               │
│                   Database (PostgreSQL)                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Submission → Form Validation → Model Save → Database
                         ↓
                   Generate Charts
                         ↓
                  AI Analysis (Optional)
                         ↓
                   Report Generation
                         ↓
                  Download/Email Report
```

### Request Flow

```
Client Request
      ↓
Django URL Routing (urls.py)
      ↓
View Function (views.py)
      ↓
Query/Update Database (models.py)
      ↓
Render Template or Return Response
      ↓
Client Response
```

---

## 📊 Data Models

### 1. **Trainer Model**
```python
Fields:
  - id: AutoField (Primary Key)
  - name: CharField(100)
  - email: EmailField
  - phone: CharField(20, blank=True)
  - specialization: CharField(200, blank=True)
  - created_at: DateTimeField(auto_now_add=True)
  - is_active: BooleanField(default=True)

Methods:
  - __str__(): Returns trainer name
  - Meta: Ordered by name
```

**Purpose**: Store trainer information and credentials

---

### 2. **TrainingSession Model**
```python
Fields:
  - id: AutoField
  - session_title: CharField(200)
  - trainer: ForeignKey(Trainer)
  - date: DateField
  - location: CharField(200, blank=True)
  - duration_hours: DecimalField (hours of training)
  - max_participants: PositiveIntegerField(default=30)
  - created_at: DateTimeField(auto_now_add=True)
  - updated_at: DateTimeField(auto_now=True)
  - is_active: BooleanField(default=True)

Methods:
  - get_feedback_count(): Returns total feedback responses
  - get_average_rating(): Calculates average of all 8 ratings
  - has_open_feedback(): Checks if session accepts feedback
  - Meta: Ordered by date (newest first)
```

**Purpose**: Represent individual training events

---

### 3. **FeedbackResponse Model**
```python
Fields:
  - id: AutoField
  - session: ForeignKey(TrainingSession)
  - participant_name: CharField(100, blank=True, default='Anonymous')
  
  Rating Fields (1-5 scale):
  - rating_1: IntegerField (Met expectations)
  - rating_2: IntegerField (Apply knowledge)
  - rating_3: IntegerField (Organized content)
  - rating_4: IntegerField (Trainer knowledgeable)
  - rating_5: IntegerField (Training relevancy)
  - rating_6: IntegerField (Clear instructions)
  - rating_7: IntegerField (Length/timing)
  - rating_8: IntegerField (Overall satisfaction)
  
  Text Fields:
  - key_learnings: TextField (Required)
  - missing_elements: TextField (Optional)
  
  Meta Fields:
  - submitted_at: DateTimeField(auto_now_add=True)
  - ip_address: GenericIPAddressField(blank=True)

Methods:
  - clean(): Validates all ratings
  - save(): Calls clean() before saving
  - get_average_rating(): Average of all 8 ratings
  - __str__(): Human-readable representation
  - Meta: Ordered by submitted_at (newest)
```

**Purpose**: Store participant feedback responses

---

### 4. **FeedbackImage Model**
```python
Fields:
  - id: AutoField
  - image: ImageField (upload_to='feedback_images/')
  - uploaded_at: DateTimeField(auto_now_add=True)
  
  Detected Ratings:
  - rating_1 to rating_8: IntegerField(null=True, blank=True)
  
  OCR Data:
  - ocr_text: TextField(blank=True)

Methods:
  - __str__(): Returns image id
```

**Purpose**: Store uploaded feedback form images and detected ratings

---

### 5. **FeedbackReport Model**
```python
Fields:
  - id: AutoField
  - session: OneToOneField(TrainingSession)
  - generated_at: DateTimeField(auto_now_add=True)
  - openai_analysis: TextField(blank=True) [AI-generated insights]
  - word_document: FileField(upload_to='reports/', blank=True)
  - email_sent: BooleanField(default=False)
  - email_sent_at: DateTimeField(null=True, blank=True)

Methods:
  - __str__(): Report identifier
  - Meta: Ordered by generated_at
```

**Purpose**: Store generated analysis reports

---

### 6. **Feedback Model** (Alternative)
```python
Fields:
  - id: AutoField
  - session: ForeignKey(TrainingSession, null=True)
  - participant_name: CharField(100, blank=True)
  - rating_1 to rating_8: IntegerField
  - key_learnings: TextField(blank=True)
  - missing_elements: TextField(blank=True)
  - submitted_at: DateTimeField(auto_now_add=True)

Methods:
  - __str__(): Descriptive representation
```

**Purpose**: Alternative feedback storage model

---

## 📁 Complete Project Structure

```
📦 Training Feedback System
│
├── 📁 training_feedback_system/        # Django Project Root
│   ├── 📁 training_feedback_system/    # Settings Package
│   │   ├── __init__.py
│   │   ├── asgi.py                     # Async gateway interface
│   │   ├── wsgi.py                     # Web server gateway
│   │   ├── settings.py                 # Development settings (135 lines)
│   │   ├── settings_production.py      # Production settings (146 lines)
│   │   └── urls.py                     # Main URL router
│   │
│   ├── 📁 feedback/                    # Main Django App
│   │   ├── __init__.py
│   │   │
│   │   ├── 📋 Core Files
│   │   ├── models.py                   # 6 Data models (203 lines)
│   │   ├── forms.py                    # Django forms (245 lines)
│   │   ├── views.py                    # Main logic (868 lines)
│   │   ├── views_admin.py              # Admin-only views
│   │   ├── views_public.py             # Public views
│   │   │
│   │   ├── 📚 Configuration & Utilities
│   │   ├── urls.py                     # URL patterns (41 routes)
│   │   ├── admin.py                    # Django admin config
│   │   ├── apps.py                     # App configuration
│   │   ├── decorators.py               # auth decorators
│   │   ├── register_view.py            # User registration
│   │   │
│   │   ├── 🤖 Advanced Features
│   │   ├── rating_detector.py          # CV-based detection (226 lines)
│   │   ├── utils.py                    # 50+ utility functions (244 lines)
│   │   │   ├── analyze_feedback_with_openai()
│   │   │   ├── create_rating_chart()
│   │   │   ├── generate_word_report()
│   │   │   ├── FeedbackAnalyzer class
│   │   │   └── send_report_email()
│   │   │
│   │   ├── 📂 Database
│   │   ├── 📁 migrations/              # Schema versions
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_*.py
│   │   │   ├── 0003_feedback.py
│   │   │   ├── 0004_feedback_session.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── 📁 templates/               # HTML Templates (26)
│   │   │   ├── feedback/
│   │   │   │   ├── base.html           # Admin base template
│   │   │   │   ├── base_public.html    # Public base template
│   │   │   │   ├── dashboard.html      # Admin dashboard
│   │   │   │   ├── session_detail.html # Session analytics
│   │   │   │   ├── session_list.html   # All sessions
│   │   │   │   ├── trainer_list.html   # All trainers
│   │   │   │   ├── create_session.html # Create session form
│   │   │   │   ├── create_trainer.html # Create trainer form
│   │   │   │   ├── edit_trainer.html   # Edit trainer form
│   │   │   │   ├── delete_session_confirm.html
│   │   │   │   ├── delete_trainer_confirm.html
│   │   │   │   ├── feedback_form.html  # Main feedback form
│   │   │   │   ├── feedback_success.html
│   │   │   │   ├── feedback_success_public.html
│   │   │   │   ├── feedback_summary.html
│   │   │   │   ├── feedback_summary_table_and_charts.html
│   │   │   │   ├── upload_feedback_image.html
│   │   │   │   ├── home.html           # Public home
│   │   │   │   ├── error.html          # Error page
│   │   │   │   ├── public_session_list.html
│   │   │   │   └── ... (more templates)
│   │   │   │
│   │   │   └── registration/           # Auth templates
│   │   │       ├── login.html
│   │   │       ├── register.html
│   │   │       ├── change_password.html
│   │   │       ├── password_reset_form.html
│   │   │       ├── password_reset_done.html
│   │   │       ├── password_reset_confirm.html
│   │   │       └── password_reset_complete.html
│   │   │
│   │   ├── 📁 templatetags/            # Custom template filters
│   │   │   ├── __init__.py
│   │   │   ├── dict_extras.py          # Dict manipulation tags
│   │   │   └── feedback_extras.py      # Feedback-specific tags
│   │   │
│   │   ├── 📁 test_images/             # Image processing tests
│   │   │   ├── fix_image.py
│   │   │   └── save_image.py
│   │   │
│   │   ├── 📁 tests/                   # Unit tests
│   │   │   └── test_ocr.py
│   │   │
│   │   ├── 🧪 Test Files
│   │   ├── tests.py                    # Django tests
│   │   ├── form_test.py
│   │   ├── quick_test.py
│   │   ├── simple_test.py
│   │   ├── test_actual.py
│   │   ├── test_actual_form.py
│   │   ├── test_detector.py
│   │   ├── test_new.py
│   │   ├── test_ratings.py
│   │   ├── test_simple.py
│   │   ├── test_output.jpg
│   │   │
│   │   └── 📦 __pycache__/             # Compiled Python cache
│   │
│   ├── 📁 templates/                   # Project-wide templates
│   │   ├── base.html                   # Main admin base
│   │   ├── base_public.html            # Main public base
│   │   ├── home.html                   # Admin home
│   │   ├── login.html                  # Login page
│   │   ├── feedback_success.html
│   │   └── registration/               # Password reset templates
│   │
│   ├── 📁 static/                      # Static assets
│   │   ├── css/
│   │   │   └── custom.css              # Custom styles
│   │   ├── images/                     # Images & icons
│   │   └── js/                         # JavaScript files
│   │
│   ├── 📁 media/                       # User-uploaded files
│   │   ├── feedback_images/            # Uploaded form images
│   │   └── reports/                    # Generated reports
│   │       └── generated/
│   │
│   ├── 📁 staticfiles/                 # Collected static files
│   │
│   ├── 🔧 Configuration & Scripts
│   ├── manage.py                       # Django CLI (79 lines)
│   ├── db.sqlite3                      # SQLite database
│   │
│   └── 📄 Project-root Files (at /Feedbacks/)
│       ├── README.md                   # Old documentation
│       ├── README_COMPLETE.md          # This file!
│       ├── requirements.txt            # Dependencies (19 packages)
│       ├── runtime.txt                 # Python version (3.12.0)
│       ├── render.yaml                 # Render.com config
│       ├── build.sh                    # Build script
│       ├── start_feedback_system.bat   # Windows startup script
│       ├── .env.example                # Environment template
│       └── .gitignore                  # Git exclusions
│
└── 🗄️ Database Schema
    ├── Trainer
    ├── TrainingSession
    ├── FeedbackResponse
    ├── FeedbackImage
    ├── FeedbackReport
    ├── Feedback
    ├── User (Django built-in)
    └── Django auth & content models
```

---

## 🚀 Installation Guide

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **Python**: 3.12.0
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 500MB for application + dependencies
- **Tesseract-OCR**: Required for image processing

### Step 1: Install System Dependencies

#### Windows
```powershell
# Install Tesseract-OCR
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Run installer and note installation path
```

#### macOS
```bash
brew install tesseract
```

#### Linux (Ubuntu)
```bash
sudo apt update
sudo apt install tesseract-ocr python3.12-dev libpq-dev
```

### Step 2: Clone Repository

```bash
cd /path/to/your/project
git clone <your-repo-url>
cd Feedbacks
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 4: Install Python Packages

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# Important variables:
# - SECRET_KEY: Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# - DEBUG: False (production), True (development)
# - ALLOWED_HOSTS: your-domain.com
# - DATABASE_URL: postgres://user:password@localhost:5432/dbname (production)
# - OPENAI_API_KEY: Your OpenAI API key (optional)
# - EMAIL_HOST_PASSWORD: Gmail app password (optional)
```

### Step 6: Database Setup

```bash
cd training_feedback_system

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
# Follow prompts (username, email, password)
```

### Step 7: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 8: Run Development Server

```bash
# From training_feedback_system directory
python manage.py runserver

# Or specify port
python manage.py runserver 0.0.0.0:8000
```

Access at: `http://localhost:8000`
Admin at: `http://localhost:8000/admin`

---

## ⚙️ Configuration

### Settings Files

#### settings.py (Development)
```python
DEBUG = True
ALLOWED_HOSTS = ['*']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3'
    }
}
```

#### settings_production.py
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
SECURE_SSL_REDIRECT = True
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://...'
    )
}
```

### Environment Variables (.env)

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/feedback

# OpenAI (Optional)
OPENAI_API_KEY=sk-...

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0
```

### Tesseract Configuration

The system auto-detects Tesseract. If manual configuration is needed:

```python
# In views.py
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 🔗 API Routes & Views

### Public Routes

| Route | Method | View | Purpose |
|-------|--------|------|---------|
| `/` | GET | `home` | Public home page |
| `/sessions/` | GET | `public_session_list` | List active sessions |
| `/form/` | GET/POST | `tabbed_feedback_forms` | Feedback form |
| `/feedback/` | GET/POST | `feedback_view` | Alternative feedback form |
| `/feedback/success/` | GET | `feedback_success` | Success page |
| `/login/` | GET/POST | Django auth | Admin login |

### Admin Routes (Requires Authentication)

| Route | Method | View | Purpose |
|-------|--------|------|---------|
| `/dashboard/` | GET | `dashboard` | Admin dashboard |
| `/sessions/list/` | GET | `session_list` | All sessions |
| `/sessions/create/` | GET/POST | `create_session` | Create session |
| `/sessions/<id>/` | GET | `session_detail` | Session details |
| `/sessions/<id>/delete/` | POST | `delete_session` | Delete session |
| `/sessions/<id>/feedback/` | GET | `session_feedback` | Session feedback |
| `/sessions/<id>/report/` | GET | `report_detail` | Report page |
| `/sessions/<id>/report/generate/` | POST | `generate_report` | Generate report |
| `/sessions/<id>/report/download/` | GET | `download_report` | Download Word doc |
| `/sessions/<id>/qr/` | GET | `download_feedback_qr` | Download QR code |
| `/sessions/<id>/toggle/` | POST | `toggle_session_active` | Activate/deactivate |
| `/trainers/` | GET | `trainer_list` | All trainers |
| `/trainers/create/` | GET/POST | `create_trainer` | Create trainer |
| `/trainers/<id>/edit/` | GET/POST | `edit_trainer` | Edit trainer |
| `/trainers/<id>/delete/` | POST | `delete_trainer` | Delete trainer |
| `/upload-feedback-image/` | POST | `upload_feedback_image` | Upload form image |
| `/feedback/summary/` | GET | `feedback_summary` | Feedback analysis |

### Authentication Routes

| Route | Purpose |
|-------|---------|
| `/login/` | Admin login |
| `/logout/` | Admin logout |
| `/password_change/` | Change password |
| `/password_reset/` | Reset password |
| `/accounts/...` | Django auth endpoints |

---

## 🧩 Key Components

### 1. AdvancedRatingDetector (rating_detector.py)

```python
class AdvancedRatingDetector:
    """Computer vision-based rating detection"""
    
    def preprocess_image(image):
        # CLAHE contrast enhancement
        # Noise reduction
        # Adaptive thresholding
        
    def detect_ratings(image):
        # Multi-feature detection
        # Confidence scoring
        # Return detected ratings
        
    def _detect_checkmark(cell):
        # Hough line detection
        # Diagonal pattern recognition
        
    def _calculate_center_score(cell):
        # Distance-weighted scoring
        
    def _calculate_edge_score(cell):
        # Edge-based confidence
```

### 2. FeedbackAnalyzer (utils.py)

```python
class FeedbackAnalyzer:
    """Analysis and report generation"""
    
    def analyze_feedback():
        # Statistical calculations
        # Average ratings
        # Sentiment analysis
        
    def generate_charts():
        # Matplotlib visualizations
        # Export as base64 images
        
    def create_word_report():
        # python-docx report generation
        # Embed charts and analysis
        # Format professionally
```

### 3. Forms (forms.py)

```python
class FeedbackForm(ModelForm):
    """Main feedback submission form"""
    - 8 rating questions (RadioSelect)
    - 2 open-ended questions
    - Crispy forms layout
    - Bootstrap styling
```

### 4. Custom Decorators (decorators.py)

```python
@admin_required
def admin_view():
    """Enforce admin authentication"""
```

---

## 🚀 Deployment Guide (EC2)

### Phase 1: EC2 Instance Setup

#### 1.1 Launch Instance
1. AWS Console → EC2 → Instances → Launch Instance
2. Select: **Ubuntu Server 22.04 LTS** (Free tier)
3. Instance Type: **t3.micro** or **t3.small**
4. Configure Security Group:
   - SSH (22): Your IP
   - HTTP (80): 0.0.0.0/0
   - HTTPS (443): 0.0.0.0/0
5. Storage: 20GB (gp3)
6. Launch and download .pem key file

#### 1.2 Elastic IP (Optional but Recommended)
```bash
aws ec2 allocate-address --domain vpc
aws ec2 associate-address --instance-id <instance-id> --allocation-id <alloc-id>
```

### Phase 2: Server Configuration

#### 2.1 SSH Connection
```powershell
# Windows PowerShell
ssh -i "C:\path\to\key.pem" ubuntu@your-ec2-ip
```

#### 2.2 System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3.12-dev python3-pip
sudo apt install -y postgresql postgresql-contrib libpq-dev
sudo apt install -y tesseract-ocr libtesseract-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y nginx gunicorn supervisor git curl wget

# Create app user
sudo useradd -m -s /bin/bash feedback_user
sudo su - feedback_user
```

### Phase 3: Database Setup

```bash
sudo su - postgres

# Create database
createdb training_feedback
createuser feedback_admin

# Set password
psql -c "ALTER USER feedback_admin WITH PASSWORD 'secure_password';"

# Grant permissions
psql -c "GRANT ALL PRIVILEGES ON DATABASE training_feedback TO feedback_admin;"

exit
```

### Phase 4: Application Deployment

```bash
cd /var/www
sudo mkdir feedback_system
sudo chown feedback_user:feedback_user feedback_system
cd feedback_system

# Clone repository
git clone <your-repo> .

# Setup Python
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Phase 5: Configure Gunicorn

Create `/etc/systemd/system/gunicorn_feedback.service`:

```ini
[Unit]
Description=Gunicorn for Feedback System
After=network.target

[Service]
Type=notify
User=feedback_user
WorkingDirectory=/var/www/feedback_system
EnvironmentFile=/var/www/feedback_system/.env
ExecStart=/var/www/feedback_system/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/feedback_system/gunicorn.sock \
    training_feedback_system.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn_feedback
sudo systemctl start gunicorn_feedback
```

### Phase 6: Configure Nginx

Create `/etc/nginx/sites-available/feedback_system`:

```nginx
upstream gunicorn {
    server unix:/var/www/feedback_system/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /var/www/feedback_system/static/;
    }

    location /media/ {
        alias /var/www/feedback_system/media/;
    }

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/feedback_system /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Phase 7: SSL Certificate (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Phase 8: Verification Checklist

- [ ] SSH access working
- [ ] PostgreSQL running
- [ ] Python venv activated
- [ ] Dependencies installed
- [ ] Migrations completed
- [ ] Static files collected
- [ ] Gunicorn service running
- [ ] Nginx service running
- [ ] HTTPS certificate active
- [ ] Website accessible

### Useful Commands

```bash
# Check service status
sudo systemctl status gunicorn_feedback
sudo systemctl status nginx

# View logs
tail -f /var/log/feedback_gunicorn.out.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart gunicorn_feedback
sudo systemctl restart nginx

# Django management
python training_feedback_system/manage.py migrate
python training_feedback_system/manage.py createsuperuser
python training_feedback_system/manage.py collectstatic --noinput
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Tesseract Not Found
```
Error: tesseract is not installed or it's not in your PATH
```

**Solution**:
```python
# Set path in settings.py or views.py
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 2. OpenCV Import Error
```
ModuleNotFoundError: No module named 'cv2'
```

**Solution**:
```bash
pip install --upgrade opencv-python
```

#### 3. Database Connection Error
```
psycopg2.OperationalError: could not connect to server
```

**Solution**:
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify DATABASE_URL in .env
- Test connection: `psql -U feedback_admin -d training_feedback`

#### 4. Static Files Not Loading
```
404 errors for CSS/JavaScript
```

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --clear --noinput

# Verify STATIC_ROOT in settings
# Check Nginx configuration
```

#### 5. Email Not Sending
```
SMTPAuthenticationError
```

**Solution**:
- Use Gmail App Password (not regular password)
- Enable "Less secure app access" if using regular Gmail
- Check EMAIL_HOST, EMAIL_PORT settings

---

## 📞 Support

### Documentation
- [Django Docs](https://docs.djangoproject.com/)
- [OpenCV Docs](https://docs.opencv.org/)
- [Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- [Render.com Docs](https://render.com/docs)

### Key Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| models.py | 203 | Data models |
| views.py | 868 | Main logic |
| forms.py | 245 | Form definitions |
| utils.py | 244 | Utility functions |
| rating_detector.py | 226 | CV algorithms |
| settings.py | 135 | Dev config |
| settings_production.py | 146 | Prod config |

---

## 📝 License & Credits

**Project**: Training Feedback System
**Status**: Production Ready
**Last Updated**: February 2026
**Python Version**: 3.12.0
**Django Version**: 3.2-4.0

---

**You're all set! Happy deploying! 🚀**
