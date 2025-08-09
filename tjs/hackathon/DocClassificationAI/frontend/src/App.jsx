import { useState, useRef } from 'react'
import { 
  CloudArrowUpIcon, 
  DocumentTextIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowPathIcon,
  EyeIcon,
  FolderIcon
} from '@heroicons/react/24/outline'

function App() { 
  const [files, setFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const API_BASE_URL = 'http://localhost:8000'

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files)
    setFiles(selectedFiles)
    setError(null)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    const droppedFiles = Array.from(event.dataTransfer.files)
    setFiles(droppedFiles)
    setError(null)
  }

  const handleDragOver = (event) => {
    event.preventDefault()
  }

  const uploadFiles = async () => {
    if (files.length === 0) {
      setError('Please select files to upload')
      return
    }

    setIsUploading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await fetch(`${API_BASE_URL}/upload-docs`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError(err.message || 'Failed to upload files')
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index))
  }

      const getDocumentTypeColor = (type) => {
        const colors = {
            rdl: 'bg-green-100 text-green-800',
            rcs: 'bg-blue-100 text-blue-800',
            rds: 'bg-teal-100 text-teal-800',
            medical_evidence: 'bg-purple-100 text-purple-800',
            lay_statement: 'bg-yellow-100 text-yellow-800',
            personal_info: 'bg-red-100 text-red-800',
            va_forms: 'bg-indigo-100 text-indigo-800',
            other: 'bg-gray-100 text-gray-800',
            unknown: 'bg-red-100 text-red-800'
        }
        return colors[type] || colors.other
    }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStatusIcon = (status) => {
    if (status === 'success') return <CheckCircleIcon className="w-5 h-5 text-green-500" />
    if (status === 'failed') return <XCircleIcon className="w-5 h-5 text-red-500" />
    return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <DocumentTextIcon className="w-8 h-8 text-primary-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">
                VA Document Classification System
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Powered by AI</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Upload Documents
          </h2>
          
          {/* File Drop Zone */}
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors cursor-pointer"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
          >
            <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg text-gray-600 mb-2">
              Drop files here or click to select
            </p>
            <p className="text-sm text-gray-500">
              Supports PDF, PNG, JPG, JPEG, TIFF, BMP files
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Selected Files */}
          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Selected Files ({files.length})
              </h3>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center">
                      <DocumentTextIcon className="w-5 h-5 text-gray-400 mr-3" />
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500 ml-2">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <XCircleIcon className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Button */}
          <div className="mt-6">
            <button
              onClick={uploadFiles}
              disabled={isUploading || files.length === 0}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isUploading ? (
                <>
                  <ArrowPathIcon className="w-5 h-5 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <CloudArrowUpIcon className="w-5 h-5 mr-2" />
                  Upload & Process Documents
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex">
                <XCircleIcon className="w-5 h-5 text-red-400 mr-2" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Results Section */}
        {results && (
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Processing Results
              </h2>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>Total: {results.total_files}</span>
                <span className="text-green-600">Success: {results.successful_files}</span>
                <span className="text-red-600">Failed: {results.failed_files}</span>
              </div>
            </div>

            <div className="space-y-4">
              {results.processed_files.map((file, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        {getStatusIcon(file.status)}
                        <h3 className="text-lg font-medium text-gray-900 ml-2">
                          {file.filename}
                        </h3>
                      </div>
                      
                                             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                         <div>
                           <label className="text-sm font-medium text-gray-500">Document Type</label>
                           <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${getDocumentTypeColor(file.document_type)}`}>
                             {file.document_type.replace('_', ' ')}
                           </div>
                         </div>
                         
                         <div>
                           <label className="text-sm font-medium text-gray-500">Veteran Name</label>
                           <p className="text-sm font-medium text-gray-900 mt-1">
                             {file.veteran_name || 'Unknown'}
                           </p>
                         </div>
                         
                         <div>
                           <label className="text-sm font-medium text-gray-500">Confidence</label>
                           <p className={`text-sm font-medium mt-1 ${getConfidenceColor(file.confidence)}`}>
                             {(file.confidence * 100).toFixed(1)}%
                           </p>
                         </div>
                         
                         <div>
                           <label className="text-sm font-medium text-gray-500">Processing Route</label>
                           <p className="text-sm text-gray-900 mt-1 capitalize">
                             {file.processing_route.replace('_', ' ')}
                           </p>
                         </div>
                       </div>

                       {/* File Information */}
                       {file.new_filename && (
                         <div className="mt-4">
                           <label className="text-sm font-medium text-gray-500">New Filename</label>
                           <p className="text-sm text-gray-700 mt-1 font-mono bg-gray-50 p-2 rounded">
                             {file.new_filename}
                           </p>
                         </div>
                       )}

                       {/* Extracted Data Section */}
                       {file.extracted_data && Object.keys(file.extracted_data).length > 0 && (
                         <div className="mt-4">
                           <label className="text-sm font-medium text-gray-500">Extracted Data</label>
                           <div className="mt-2 bg-blue-50 rounded-lg p-3">
                             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                               {Object.entries(file.extracted_data).map(([key, value]) => {
                                 // Skip internal fields
                                 if (['extraction_timestamp', 'document_type'].includes(key)) return null;
                                 
                                 // Format the key for display
                                 const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                                 
                                 // Handle different value types
                                 let displayValue = value;
                                 if (typeof value === 'object' && value !== null) {
                                   displayValue = JSON.stringify(value, null, 2);
                                 } else if (typeof value === 'string' && value.length > 50) {
                                   displayValue = value.substring(0, 50) + '...';
                                 }
                                 
                                 return (
                                   <div key={key} className="text-sm">
                                     <span className="font-medium text-gray-700">{displayKey}:</span>
                                     <span className="ml-1 text-gray-600">{displayValue}</span>
                                   </div>
                                 );
                               })}
                             </div>
                           </div>
                         </div>
                       )}

                      {file.classification_reasoning && (
                        <div className="mt-3">
                          <label className="text-sm font-medium text-gray-500">Reasoning</label>
                          <p className="text-sm text-gray-700 mt-1">{file.classification_reasoning}</p>
                        </div>
                      )}

                      {file.error && (
                        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                          <p className="text-sm text-red-700">{file.error}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Info */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="flex items-center">
              <FolderIcon className="w-8 h-8 text-primary-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-gray-900">Auto-Processed</h3>
                <p className="text-sm text-gray-500">High confidence documents</p>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center">
              <EyeIcon className="w-8 h-8 text-yellow-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-gray-900">Human Review</h3>
                <p className="text-sm text-gray-500">Medium confidence documents</p>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center">
              <XCircleIcon className="w-8 h-8 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-gray-900">Rejected</h3>
                <p className="text-sm text-gray-500">Low confidence documents</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
