# WhatsApp Business API Onboarding Portal

A modern web application that helps businesses onboard to WhatsApp Business API through Meta's platform. This project has been converted from a Flask template-based application to a React frontend with Flask API backend.

## 🚀 Features

### Core Functionality
- **User Authentication**: Registration and login system with session management
- **Document Upload**: Upload PAN and GST documents with file validation
- **WhatsApp Business Integration**: OAuth flow with Meta for WhatsApp Business Account setup
- **Message Template Management**: Create and manage WhatsApp message templates
- **Message Sending**: Send WhatsApp messages using approved templates
- **Message History**: Track sent messages and delivery status
- **Admin Panel**: User management and status oversight

### Technical Stack
- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: React with Bootstrap 5
- **Database**: MySQL
- **API**: RESTful API with JSON responses
- **Authentication**: Flask-Login with session management
- **File Upload**: Secure file handling with validation

## 📁 Project Structure

```
wa_bridge/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── api_routes.py        # API endpoints (NEW)
│   ├── admin_routes.py      # Admin panel routes
│   ├── models.py            # Database models
│   ├── forms.py             # Form definitions
│   └── templates/           # Legacy templates (can be removed)
├── frontend/                # React application (NEW)
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Navbar.js
│   │   │   ├── Home.js
│   │   │   ├── Login.js
│   │   │   ├── Register.js
│   │   │   ├── Dashboard.js
│   │   │   └── ManageTemplates.js
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── index.css
│   │   └── App.css
│   └── package.json
├── config.py                # Configuration settings
├── run.py                   # Flask application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL database
- Meta Developer Account (for WhatsApp Business API)

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure database**:
   - Create MySQL database: `whatsapp_onboarding`
   - Update database connection in `config.py`

3. **Initialize database**:
   ```python
   from app import create_app, db
   app = create_app()
   with app.app_context():
       db.create_all()
   ```

4. **Update Meta configuration**:
   - Update `META_APP_ID`, `META_APP_SECRET`, and `META_REDIRECT_URI` in `config.py`
   - Set up webhook URL in Meta Developer Console

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

## 🚀 Running the Application

### Development Mode

1. **Start Flask backend** (from project root):
   ```bash
   python run.py
   ```
   Backend will run on `http://localhost:5000`

2. **Start React frontend** (from frontend directory):
   ```bash
   npm start
   ```
   Frontend will run on `http://localhost:3000`

### Production Mode

1. **Build React frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Serve static files with Flask** (update `run.py` to serve React build)

## 🔧 API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/user/status` - Get current user status

### Dashboard
- `GET /api/dashboard` - Get dashboard data
- `POST /api/upload` - Upload documents
- `GET /api/onboard/start` - Start WhatsApp onboarding
- `GET /api/onboard/callback` - OAuth callback

### Templates
- `GET /api/templates` - Get user templates
- `POST /api/templates` - Create new template

### Messaging
- `POST /api/send-message` - Send WhatsApp message
- `POST /api/webhook/meta` - Meta webhook for status updates

## 🔐 Security Features

- Password hashing with Werkzeug
- CSRF protection
- Secure file uploads with validation
- Session management with Flask-Login
- CORS configuration for API access

## 📱 WhatsApp Integration Flow

1. **Document Upload**: Users upload PAN and GST documents
2. **Meta OAuth**: Redirect to Meta for WhatsApp Business Account authorization
3. **Credential Storage**: Store access tokens and account IDs
4. **Template Creation**: Create and submit message templates to Meta
5. **Message Sending**: Send messages using approved templates
6. **Status Tracking**: Monitor delivery status via webhooks

## 🎨 UI/UX Features

- **Responsive Design**: Mobile-friendly interface
- **Modern UI**: Bootstrap 5 with custom styling
- **Animations**: Smooth fade-in effects
- **Real-time Feedback**: Loading states and alerts
- **Intuitive Navigation**: Clear step-by-step process

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `META_APP_ID`: Meta App ID
- `META_APP_SECRET`: Meta App Secret
- `META_REDIRECT_URI`: OAuth redirect URI

### File Upload Settings
- Maximum file size: 16MB
- Allowed extensions: PDF, JPG, PNG, JPEG
- Upload folder: `uploads/`

## 🚀 Deployment

### Backend Deployment
1. Set up production WSGI server (Gunicorn)
2. Configure environment variables
3. Set up database migrations
4. Configure webhook endpoints

### Frontend Deployment
1. Build React application: `npm run build`
2. Serve static files with Flask or separate web server
3. Configure API proxy settings

## 📊 Database Schema

### Users
- `id`: Primary key
- `email`: User email (unique)
- `password`: Hashed password
- `onboarding_status`: Pending/In Progress/Verified
- `waba_id`: WhatsApp Business Account ID
- `phone_number_id`: Phone number ID
- `whatsapp_access_token`: Access token

### Uploads
- `id`: Primary key
- `filename`: Uploaded file name
- `filetype`: PAN or GST
- `user_id`: Foreign key to User

### Templates
- `id`: Primary key
- `user_id`: Foreign key to User
- `name`: Template name
- `content`: Message content
- `status`: Pending/Approved/Rejected
- `meta_template_id`: Meta's template ID

### MessageHistory
- `id`: Primary key
- `user_id`: Foreign key to User
- `recipient`: Phone number
- `template_id`: Foreign key to Template
- `status`: Message delivery status
- `created_at`: Timestamp

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the API endpoints
- Test with the provided examples
- Create an issue for bugs or feature requests