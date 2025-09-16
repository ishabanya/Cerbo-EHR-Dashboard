# 🏥 Health Management System

<div align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS">
</div>

<div align="center">
  <h3>🚀 A modern, full-stack health management application</h3>
  <p>Built with FastAPI, Next.js, and TypeScript with <strong>Cerbo Sandbox API</strong> integration</p>
  <p>🔗 <em>Integrated with Cerbo Healthcare Platform for real-world EHR functionality</em></p>
</div>

---

## ✨ Features

<table>
  <tr>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/patient.png" width="40" height="40"/>
      <br><b>Patient Management</b>
      <br>Complete patient profiles with demographics, contact info, and medical history
    </td>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/calendar.png" width="40" height="40"/>
      <br><b>Appointment Scheduling</b>
      <br>Intuitive scheduling system with conflict detection and status tracking
    </td>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/medical-history.png" width="40" height="40"/>
      <br><b>Clinical Records</b>
      <br>Comprehensive medical records, vital signs, and treatment history
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/doctor-male.png" width="40" height="40"/>
      <br><b>Provider Management</b>
      <br>Healthcare provider profiles with specialties and availability
    </td>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/insurance.png" width="40" height="40"/>
      <br><b>Insurance Tracking</b>
      <br>Insurance coverage management and eligibility verification
    </td>
    <td align="center">
      <img src="https://img.icons8.com/fluency/48/000000/money-bag.png" width="40" height="40"/>
      <br><b>Billing System</b>
      <br>Integrated billing with payment tracking and claims processing
    </td>
  </tr>
</table>

### 🔗 Cerbo Sandbox Integration

This application integrates with the **Cerbo Healthcare Platform** through their sandbox API, providing:

- **Real-time EHR Data Sync** - Bidirectional synchronization with Cerbo's healthcare platform
- **Patient Data Management** - Seamless patient record creation and updates
- **Appointment Coordination** - Integration with Cerbo's scheduling system
- **Clinical Workflow** - Support for real-world healthcare workflows
- **API Authentication** - Secure connection to Cerbo's sandbox environment

> 💡 **Note**: This system uses Cerbo's sandbox environment for development and testing purposes, enabling realistic healthcare data workflows without affecting production systems.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Cerbo API     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Sandbox)     │
│                 │    │                 │    │                 │
│ • React 18      │    │ • Python 3.8+   │    │ • Patient Data  │
│ • TypeScript    │    │ • SQLAlchemy    │    │ • Appointments  │
│ • Tailwind CSS  │    │ • Alembic       │    │ • Clinical Data │
│ • Custom UI     │    │ • SQLite/PostgreSQL│ │ • Provider Info │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   User Interface│    │   Database      │
│                 │    │                 │
│ • Dashboard     │    │ • Patients      │
│ • Patient Mgmt  │    │ • Appointments  │
│ • Scheduling    │    │ • Clinical Recs │
│ • Billing       │    │ • Providers     │
└─────────────────┘    └─────────────────┘
```

### Backend (FastAPI)
- **🐍 Python 3.8+** - Modern async/await support
- **⚡ FastAPI** - High-performance web framework
- **🗃️ SQLAlchemy** - Powerful ORM with relationship mapping
- **🔄 Alembic** - Database migration management
- **📊 SQLite/PostgreSQL** - Flexible database options

### Frontend (Next.js)
- **⚛️ React 18** - Modern component-based UI
- **📘 TypeScript** - Type-safe development
- **🎨 Tailwind CSS** - Utility-first styling
- **🔧 Custom Components** - Reusable UI library
- **📱 Responsive Design** - Mobile-first approach

## 🚀 Quick Start

### Prerequisites
```bash
# Required software
Python 3.8+
Node.js 16+
npm or yarn
```

### 1️⃣ Backend Setup
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Cerbo Sandbox (optional)
cp .env.example .env
# Edit .env with your Cerbo sandbox credentials

# Initialize database
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### 2️⃣ Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3️⃣ Access the Application
- 🌐 **Frontend**: http://localhost:3000
- 🔗 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

## 📊 API Documentation

The API provides comprehensive endpoints for healthcare data management with automatic interactive documentation available at `/docs` when running the backend server.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/patients` | List all patients |
| `POST` | `/api/v1/patients` | Create new patient |
| `GET` | `/api/v1/appointments` | Get appointments |
| `POST` | `/api/v1/appointments` | Schedule appointment |
| `GET` | `/api/v1/clinical-records` | Retrieve clinical records |
| `POST` | `/api/v1/clinical-records` | Add clinical record |

## 🎨 Application Features

### 📱 **Dashboard Overview**
- Real-time patient statistics and metrics
- Quick access to recent appointments and clinical records
- Provider availability and scheduling overview
- Integrated billing and insurance status

### 👥 **Patient Management**
- Comprehensive patient profiles with demographics
- Medical history and clinical record tracking
- Insurance information and coverage verification
- Emergency contact and family history management

### 📅 **Appointment Scheduling**
- Intuitive calendar interface with conflict detection
- Provider availability and specialty filtering
- Automated reminders and notifications
- Recurring appointment support

### 🏥 **Clinical Records**
- Detailed medical history documentation
- Vital signs tracking and trending
- Treatment plans and medication management
- Lab results and diagnostic imaging integration

### 💰 **Billing & Insurance**
- Automated billing generation and tracking
- Insurance eligibility verification
- Payment processing and claims management
- Financial reporting and analytics

## 🛠️ Development

### Project Structure
```
health/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   ├── schemas/        # Pydantic schemas
│   │   └── utils/          # Utilities
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Next.js pages
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── styles/         # CSS styles
│   └── package.json        # Node dependencies
└── README.md              # This file
```

### Available Scripts

#### Backend
```bash
# Start development server
uvicorn app.main:app --reload

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Add sample data
python add_sample_data.py
```

#### Frontend
```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database Configuration
DATABASE_URL=sqlite:///./ehr_dashboard.db
DEBUG=True
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["http://localhost:3000"]

# Cerbo Sandbox API (Optional)
CERBO_BASE_URL=https://sandbox.md-hq.com/api/v1
CERBO_USERNAME=your_sandbox_username
CERBO_SECRET_KEY=your_sandbox_secret_key
```

> 🔐 **Cerbo Sandbox Setup**: To enable Cerbo integration, sign up for a Cerbo sandbox account and add your credentials to the `.env` file. The application works without Cerbo integration for local development.

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME="Health Management System"
```

## 📈 Performance

<div align="center">
  <table>
    <tr>
      <th>Metric</th>
      <th>Score</th>
      <th>Status</th>
    </tr>
    <tr>
      <td>First Contentful Paint</td>
      <td>&lt; 1.5s</td>
      <td>✅</td>
    </tr>
    <tr>
      <td>Largest Contentful Paint</td>
      <td>&lt; 2.5s</td>
      <td>✅</td>
    </tr>
    <tr>
      <td>Cumulative Layout Shift</td>
      <td>&lt; 0.1</td>
      <td>✅</td>
    </tr>
    <tr>
      <td>First Input Delay</td>
      <td>&lt; 100ms</td>
      <td>✅</td>
    </tr>
  </table>
</div>

## 🏥 Cerbo Healthcare Platform Integration

This application leverages the **Cerbo Sandbox API** to provide realistic healthcare data management capabilities:

### 🔗 **Integration Features**
- **Patient Synchronization** - Sync patient data between local database and Cerbo platform
- **Appointment Management** - Create and manage appointments through Cerbo's scheduling system
- **Clinical Data Exchange** - Exchange clinical records and medical information
- **Provider Network** - Access to Cerbo's provider directory and profiles
- **Insurance Verification** - Real-time insurance eligibility checking through Cerbo

### 🛠️ **API Capabilities**
```python
# Example Cerbo integration usage
await cerbo_client.create_patient(patient_data)
await cerbo_client.schedule_appointment(appointment_data)
await cerbo_client.sync_clinical_records(patient_id)
```

### 📚 **Cerbo Resources**
- **Sandbox Environment**: [https://sandbox.md-hq.com/](https://sandbox.md-hq.com/)
- **API Documentation**: [https://docs.cer.bo/](https://docs.cer.bo/)
- **Developer Portal**: Access through Cerbo's developer program

## 🔒 Security Features

- 🛡️ **Input Validation** - Comprehensive data validation with Pydantic
- 🔐 **CORS Protection** - Configurable cross-origin resource sharing
- 🚫 **SQL Injection Prevention** - ORM-based database queries
- 🔒 **Environment Variables** - Secure configuration management
- 📝 **Request Logging** - Comprehensive audit trail
- 🔐 **Cerbo API Security** - Secure authentication with Cerbo's healthcare platform

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 📦 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
```bash
# Backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
npm run build && npm start
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - For the excellent web framework
- **Next.js** - For the powerful React framework
- **Tailwind CSS** - For the utility-first CSS framework
- **SQLAlchemy** - For the robust ORM
- **Icons8** - For the beautiful icons

---

<div align="center">
  <p>Made with ❤️ for better healthcare management</p>
  <p>
    <a href="#health-management-system">⬆️ Back to top</a>
  </p>
</div>