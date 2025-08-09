# VA Document Classification System - Frontend

A modern React frontend for the VA Document Classification System, built with Vite, Tailwind CSS, and Heroicons.

## 🚀 Features

- **Drag & Drop File Upload**: Easy file selection with drag and drop support
- **Real-time Processing**: Live updates during document processing
- **Beautiful Results Display**: Clean, organized display of classification results
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Modern UI**: Built with Tailwind CSS for a professional look

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Heroicons** - Beautiful SVG icons
- **Headless UI** - Accessible UI components

## 📦 Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5173`

## 🔧 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles with Tailwind
├── public/              # Static assets
├── index.html           # HTML template
├── tailwind.config.js   # Tailwind configuration
├── postcss.config.js    # PostCSS configuration
└── package.json         # Dependencies and scripts
```

## 🎨 UI Components

### File Upload
- Drag and drop interface
- Multiple file selection
- File size display
- Remove individual files

### Results Display
- Document type badges with color coding
- Confidence scores with visual indicators
- Processing route information
- Error handling and display

### Status Indicators
- Success/failure icons
- Color-coded confidence levels
- Processing status updates

## 🔗 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`:

- **POST /upload-docs** - Upload and process documents
- **GET /health** - Health check
- **GET /stats** - Processing statistics

## 🎯 Usage

1. **Upload Documents**: Drag and drop or click to select PDF/image files
2. **Process**: Click "Upload & Process Documents" to start classification
3. **View Results**: See classification results, confidence scores, and processing routes
4. **Monitor**: Track success/failure rates and document types

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment.

### Environment Variables

The frontend is configured to connect to the backend at `http://localhost:8000`. For production, update the `API_BASE_URL` in `src/App.jsx`.

## 🎨 Customization

### Colors
Update the color scheme in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        50: '#eff6ff',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
      }
    }
  },
}
```

### Document Types
Add new document types in the `getDocumentTypeColor` function in `App.jsx`.

### Styling
All styling is done with Tailwind CSS utility classes. Custom styles can be added to `src/index.css`.

## 🔧 Troubleshooting

### Common Issues

1. **Backend Connection**: Ensure the FastAPI backend is running on port 8000
2. **CORS Issues**: The backend includes CORS middleware for frontend integration
3. **File Upload**: Check that files are in supported formats (PDF, PNG, JPG, etc.)

### Development Tips

- Use the browser's developer tools to debug API calls
- Check the Network tab for request/response details
- Use React Developer Tools for component debugging

## 📄 License

This project is licensed under the MIT License.
