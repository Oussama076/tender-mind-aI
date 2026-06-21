import { Toaster } from 'sonner'
import Dashboard from './components/Dashboard'

function App() {
  return (
    <div className="min-h-screen bg-[#09090b] font-sans">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#18181b',
            border: '1px solid #27272a',
            color: '#fafafa',
            fontSize: '13px',
          },
        }}
        richColors
        closeButton
      />
      <Dashboard />
    </div>
  )
}

export default App
