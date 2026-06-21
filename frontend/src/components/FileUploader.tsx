import { useState, useCallback } from 'react'
import { UploadCloud, FileUp, X, Loader2 } from 'lucide-react'
import axios from 'axios'
import { toast } from 'sonner'

interface FileUploaderProps {
  onUploadSuccess?: () => void
}

const FileUploader = ({ onUploadSuccess }: FileUploaderProps) => {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (file) {
      setIsUploading(true)
      const toastId = toast.loading('Uploading and extracting document...')
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        await axios.post('/upload/rfp', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        toast.success('RFP uploaded and indexed successfully!', { id: toastId })
        setFile(null)
        if (onUploadSuccess) onUploadSuccess()
      } catch (error) {
        toast.error('Failed to upload RFP.', { id: toastId })
      } finally {
        setIsUploading(false)
      }
    }
  }

  const clearFile = () => setFile(null)

  return (
    <div className="card p-6 mb-8">
      <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
        Upload New RFP
      </h3>

      <div
        className={`
          relative border-2 border-dashed rounded-xl p-10
          flex flex-col items-center justify-center
          transition-all duration-300 cursor-pointer group
          ${isDragging
            ? 'border-brand-500 bg-brand-500/5'
            : 'border-zinc-700 bg-zinc-800/30 hover:border-zinc-500 hover:bg-zinc-800/60'
          }
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={`
          p-4 rounded-full mb-4 transition-colors duration-300
          ${isDragging ? 'bg-brand-500/10' : 'bg-zinc-800 group-hover:bg-zinc-700'}
        `}>
          <UploadCloud className={`
            w-8 h-8 transition-colors duration-300
            ${isDragging ? 'text-brand-400' : 'text-zinc-500 group-hover:text-zinc-300'}
          `} />
        </div>

        <p className="text-zinc-300 font-medium mb-1">
          Drag and drop your RFP document
        </p>
        <p className="text-zinc-500 text-sm mb-5">
          PDF or Word • Max 50MB
        </p>

        <label className="btn-primary text-sm flex items-center gap-2 cursor-pointer">
          <FileUp className="w-4 h-4" />
          Browse Files
          <input
            type="file"
            className="hidden"
            accept=".pdf,.doc,.docx"
            onChange={handleFileSelect}
          />
        </label>
      </div>

      {/* Selected File Preview */}
      {file && (
        <div className="mt-4 flex items-center justify-between bg-zinc-800 border border-zinc-700 p-4 rounded-lg animate-in fade-in">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-brand-500/10 rounded-lg shrink-0">
              <FileUp className="w-4 h-4 text-brand-400" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-zinc-200 font-medium truncate">{file.name}</p>
              <p className="text-xs text-zinc-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 ml-4">
            <button 
              onClick={handleUpload} 
              disabled={isUploading}
              className="btn-success text-sm py-1.5 px-4 flex items-center gap-2"
            >
              {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Upload
            </button>
            <button
              onClick={clearFile}
              className="p-1.5 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUploader
