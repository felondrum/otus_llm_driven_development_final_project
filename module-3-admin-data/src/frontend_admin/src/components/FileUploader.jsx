import React, { useState } from 'react'

const FileUploader = ({ 
  label = 'Upload File',
  acceptedFiles = '.csv,.json,.txt',
  maxFileSize = 10 * 1024 * 1024,
  onUpload,
  onClear
}) => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      validateAndSetFile(file)
    }
  }

  const validateAndSetFile = (file) => {
    setError(null)

    // Check file type
    const allowedTypes = acceptedFiles.split(',').map(t => t.trim())
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    
    if (!allowedTypes.includes(fileExtension) && !allowedTypes.includes(file.type)) {
      setError(`Invalid file type. Allowed: ${acceptedFiles}`)
      return
    }

    // Check file size
    if (file.size > maxFileSize) {
      setError(`File too large. Max size: ${maxFileSize / (1024 * 1024)}MB`)
      return
    }

    setSelectedFile(file)
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    setProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Simulate progress
      for (let i = 0; i <= 100; i += 10) {
        setProgress(i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      if (onUpload) {
        const result = await onUpload(selectedFile, formData)
        setProgress(100)
        return result
      }
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setProgress(0)
    setError(null)
    if (onClear) {
      onClear()
    }
  }

  return (
    <div className="file-uploader">
      <label className="file-label">{label}</label>
      
      <div className="file-input-wrapper">
        <input
          type="file"
          accept={acceptedFiles}
          onChange={handleFileSelect}
          disabled={uploading}
        />
      </div>

      {selectedFile && (
        <div className="file-info">
          <span className="filename">{selectedFile.name}</span>
          <span className="filesize">{(selectedFile.size / 1024).toFixed(2)} KB</span>
          <button onClick={handleClear} className="btn btn-sm btn-secondary">
            Clear
          </button>
        </div>
      )}

      {uploading && (
        <div className="progress-container">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
          <span>{progress}%</span>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        className="btn btn-primary upload-btn"
      >
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  )
}

export default FileUploader
