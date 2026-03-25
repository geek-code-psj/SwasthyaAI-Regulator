# SwasthyaAI Regulator - Frontend

A professional, production-ready React frontend for government healthcare regulatory document processing and compliance management.

## 📋 Features

- **🔐 JWT Authentication** - Secure token-based authentication
- **📄 Document Upload** - Drag-and-drop file upload with validation (PDF, JPEG, PNG, TIFF)
- **⏱️ Real-time Processing** - Live status polling with multi-stage pipeline visualization
- **✅ Compliance Reporting** - 4-framework regulatory assessment (DPDP, NDHM, ICMR, CDSCO)
- **🤖 AI Processing** - OCR extraction, anonymization, summarization
- **📊 Dashboard** - Submissions management with pagination and filtering
- **🎨 Professional UI** - TailwindCSS-based healthcare/government design
- **📱 Responsive** - Mobile-first design for desktop, tablet, and mobile

## 🏗️ Architecture

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Header.jsx       # Navigation header
│   │   └── Sidebar.jsx      # Left sidebar menu
│   ├── pages/               # Page components
│   │   ├── Login.jsx        # Authentication page
│   │   ├── Dashboard.jsx    # Main dashboard
│   │   ├── Upload.jsx       # File upload page
│   │   ├── ProcessingStatus.jsx  # Real-time processing
│   │   ├── Results.jsx      # Display results
│   │   ├── Compliance.jsx   # Compliance report
│   │   ├── Settings.jsx     # User settings
│   │   └── NotFound.jsx     # 404 page
│   ├── services/
│   │   └── api.js           # API client with interceptors
│   ├── stores/
│   │   └── index.js         # Zustand state management
│   ├── App.jsx              # Main app with routing
│   ├── App.css              # Global styles
│   └── main.jsx             # Entry point
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # TailwindCSS configuration
├── postcss.config.js        # PostCSS configuration
├── .env.local               # Environment variables
├── package.json             # Dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm 8+ or yarn
- Backend API running on `http://localhost:5000`

### Installation

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Set Environment Variables**
   
   Create `.env.local` file (already included):
   ```env
   VITE_API_URL=http://localhost:5000/api
   VITE_APP_NAME=SwasthyaAI Regulator
   VITE_ENVIRONMENT=development
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```
   
   The app will open at `http://localhost:5173` (or the next available port)

### Build for Production
```bash
npm run build
npm run preview  # Test production build locally
```

## 🔗 API Integration

The frontend connects to backend API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/token` | POST | Get authentication token |
| `/api/submissions/upload` | POST | Upload document file |
| `/api/submissions/{id}/status` | GET | Get processing status |
| `/api/submissions/{id}/results` | GET | Get processing results |
| `/api/submissions` | GET | List all submissions |

### Request/Response Flow

```
Login Page
  ↓ (POST /auth/token)
Dashboard (localStorage token)
  ↓ (Navigate or Upload)
Upload Page
  ↓ (POST /submissions/upload + FormData)
ProcessingStatus (Real-time polling)
  ↓ (GET /submissions/{id}/status every 3s)
Results Page (on completion)
  ↓ (GET /submissions/{id}/results)
Compliance Report (displays assessment)
```

## 🔐 Authentication

- **Token Storage**: JWT stored in `localStorage` as `auth_token`
- **Auto-injection**: Token automatically added to all API requests via interceptor
- **Error Handling**: 401 responses trigger redirect to `/login`
- **Protected Routes**: `ProtectedRoute` component guards authenticated pages

## 📦 Dependencies

### Core
- **react** - UI library
- **react-dom** - DOM rendering
- **react-router-dom** - Client-side routing
- **zustand** - State management (lightweight)
- **axios** - HTTP client

### UI Components
- **react-helmet-async** - Metadata management
- **react-hot-toast** - Notifications
- **lucide-react** - Icon library
- **tailwindcss** - Utility CSS framework

### Utilities
- **date-fns** - Date formatting
- **postcss** - CSS processing
- **autoprefixer** - CSS vendor prefixes

## 🎨 Styling

### TailwindCSS Customization
- Custom color palette (blue/professional)
- Component classes: `.btn-primary`, `.btn-secondary`, `.card`, etc.
- Animations: `slideIn`, `fadeIn`, `pulse-subtle`
- Responsive design with `md:`, `lg:` breakpoints

### Custom Classes (App.css)
```css
.btn-primary        /* Primary action button */
.btn-secondary      /* Secondary action button */
.btn-danger         /* Danger/destructive action */
.btn-success        /* Success action */
.card               /* Card container */
.input-field        /* Form input styling */
.badge              /* Status badge */
.progress-bar       /* Progress indicator */
```

## 🔄 State Management (Zustand)

### Auth Store
```javascript
const { token, isAuthenticated, setToken, logout } = useAuthStore();
```

### Submissions Store
```javascript
const { 
  submissions, 
  currentSubmission, 
  loading, 
  error,
  addSubmission,
  updateSubmission 
} = useSubmissionStore();
```

## 📱 Responsive Design

- **Mobile** (<640px): Single column, collapsible sidebar
- **Tablet** (640px-1024px): Two column, responsive layout
- **Desktop** (>1024px): Full sidebar, multi-column grids

## 📄 Component Documentation

### Login Page
- Displays authentication form
- Shows system status
- Feature grid of 4 compliance frameworks
- Handles JWT token acquisition and storage

### Dashboard
- Stats cards (Total, Processing, Completed, Failed)
- Submissions table with pagination
- Action buttons for viewing results/compliance
- New Submission CTA button

### Upload Page
- Drag-and-drop file upload
- File validation (size: 100MB max, types: PDF/JPG/PNG/TIFF)
- Document type selection (form_44, form_md26, drug_dossier)
- Processing pipeline visualization
- Key features sidebar

### ProcessingStatus Page
- Real-time polling (every 3 seconds)
- Multi-stage pipeline visualization
- Current status badge
- Elapsed time and progress percentage
- Auto-refresh toggle

### Results Page
- Document summary display
- PII statistics with visualization
- Anonymized text preview (expandable)
- Compliance status (4 frameworks)
- Download results button

### Compliance Report
- 4-framework assessment (DPDP, NDHM, ICMR, CDSCO)
- Individual compliance scores (0-100)
- Requirements checklist
- Recommendations section
- Download report button
- Overall compliance status

### Settings Page
- Profile management (name, email, organization, role)
- Security settings (password, 2FA, sessions)
- Notification preferences (email, digest)
- Data retention policies
- Storage usage display
- Logout functionality

## 🐛 Troubleshooting

### CORS Issues
- Ensure backend is running on `http://localhost:5000`
- Check `vite.config.js` proxy configuration
- Verify `/api` proxy points to correct backend URL

### 401 Unauthorized
- Check if auth token exists in localStorage
- Verify token hasn't expired
- Try logging in again

### File Upload Fails
- Validate file size (max 100MB)
- Check file type (PDF, JPG, PNG, TIFF only)
- Ensure backend `/upload` endpoint is running

### Styling Issues
- Run `npm run build` to verify TailwindCSS compilation
- Check `tailwind.config.js` for correct content paths
- Clear browser cache and rebuild if styles missing

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:5000/api` | Backend API base URL |
| `VITE_APP_NAME` | `SwasthyaAI Regulator` | Application name |
| `VITE_ENVIRONMENT` | `development` | Environment (development/production) |

## 📚 Project Standards

- **Code Style**: ES6+ with React hooks
- **Naming**: camelCase for files, PascalCase for components
- **Linting**: ESLint configured (run with `npm run lint`)
- **Formatting**: Prettier configured (run with `npm run format`)

## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/new-feature`)
2. Commit changes (`git commit -m 'Add new feature'`)
3. Push to branch (`git push origin feature/new-feature`)
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Related

- [Backend Documentation](../backend/README.md)
- [Compliance Frameworks](./COMPLIANCE.md)
- [API Documentation](./API.md)

## 🎯 Roadmap

- [ ] Multi-language support (Hindi, Bengali)
- [ ] PDF export of reports
- [ ] Advanced filtering and search
- [ ] Offline mode support
- [ ] Mobile app (React Native)
- [ ] WebSocket for real-time updates
- [ ] Advanced analytics dashboard
- [ ] Audit log viewer

## 📞 Support

For issues or questions:
- Check existing GitHub issues
- Create new issue with detailed description
- Contact: support@swasthyai.gov

## 🏥 Healthcare Compliance

This platform adheres to:
- **DPDP Act** - Digital Personal Data Protection
- **NDHM** - National Digital Health Mission
- **ICMR** - Indian Council of Medical Research
- **CDSCO** - Central Drugs Standard Control Organization

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: 🟢 Production Ready
