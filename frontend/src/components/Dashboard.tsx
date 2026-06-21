import { useEffect, useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import {
  Activity,
  CheckCircle,
  FileText,
  RefreshCw,
  Play,
  ShieldAlert,
  ChevronDown,
  Loader2,
  Zap,
  Search,
  Shield,
  Inbox,
} from 'lucide-react'
import FileUploader from './FileUploader'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */
interface RFPItem {
  id: string
  name: string
}

/* ------------------------------------------------------------------ */
/*  Dashboard Component                                                */
/* ------------------------------------------------------------------ */
const Dashboard = () => {
  // Data
  const [rfps, setRfps] = useState<RFPItem[]>([])
  const [selectedRfp, setSelectedRfp] = useState('')
  const [focusArea, setFocusArea] = useState('General requirements and deliverables')

  // Workflow state
  const [isIngesting, setIsIngesting] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [analystFindings, setAnalystFindings] = useState<string | null>(null)
  const [strategyAssessment, setStrategyAssessment] = useState<string | null>(null)
  const [legalReview, setLegalReview] = useState<string | null>(null)
  const [awaitingApproval, setAwaitingApproval] = useState(false)
  const [finalProposal, setFinalProposal] = useState<string | null>(null)

  const isBusy = isIngesting || isAnalyzing || isGenerating

  /* ------ API helpers ------ */

  const fetchRfps = async () => {
    try {
      const res = await axios.get('/list-rfps')
      if (res.data.status === 'success') {
        const mapped: RFPItem[] = res.data.rfps.map((r: any) =>
          typeof r === 'string' ? { id: r, name: r } : r
        )
        setRfps(mapped)
        if (mapped.length > 0 && !selectedRfp) setSelectedRfp(mapped[0].id)
      }
    } catch {
      setRfps([])
    }
  }

  useEffect(() => { fetchRfps() }, [])

  const handleIngest = async () => {
    if (!selectedRfp) return
    setIsIngesting(true)
    const fileName = rfps.find(r => r.id === selectedRfp)?.name || 'Document'
    toast.loading(`Indexing ${fileName}…`, { id: 'ingest' })
    try {
      await axios.post('/ingest/drive', { file_id: selectedRfp })
      toast.success(`${fileName} indexed successfully`, { id: 'ingest' })
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message, { id: 'ingest' })
    } finally {
      setIsIngesting(false)
    }
  }

  const runPreReview = async () => {
    setIsAnalyzing(true)
    setAnalystFindings(null)
    setStrategyAssessment(null)
    setLegalReview(null)
    setFinalProposal(null)
    toast.loading('Running Analyst, Strategy & Legal agents…', { id: 'analyze' })
    try {
      const res = await axios.post('/analyze', { 
        focus_area: focusArea,
        rfp_id: selectedRfp 
      })
      if (res.data.status === 'success') {
        setAnalystFindings(res.data.analyst_findings)
        setStrategyAssessment(res.data.strategy_assessment)
        setLegalReview(res.data.legal_review)
        setAwaitingApproval(true)
        toast.success('Analysis complete — review required', { id: 'analyze' })
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message, { id: 'analyze' })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const approveAndGenerate = async () => {
    setAwaitingApproval(false)
    setIsGenerating(true)
    toast.loading('Generating proposal…', { id: 'generate' })
    try {
      const res = await axios.post('/write_proposal', {
        analyst_output: analystFindings,
        strategy_output: strategyAssessment,
        legal_output: legalReview,
      })
      if (res.data.status === 'success') {
        setFinalProposal(res.data.final_proposal)
        toast.success('Proposal generated successfully', { id: 'generate' })
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || err.message, { id: 'generate' })
    } finally {
      setIsGenerating(false)
    }
  }

  const rejectAnalysis = () => {
    setAwaitingApproval(false)
    setAnalystFindings(null)
    setStrategyAssessment(null)
    setLegalReview(null)
    toast.info('Analysis rejected by user')
  }

  const resetState = () => {
    setAnalystFindings(null)
    setStrategyAssessment(null)
    setLegalReview(null)
    setFinalProposal(null)
    setAwaitingApproval(false)
    toast.success('Workspace reset. Ready for a new analysis.')
  }

  const hasResults = analystFindings || strategyAssessment || legalReview || finalProposal || awaitingApproval

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */
  return (
    <div className="flex h-screen overflow-hidden bg-[#09090b]">

      {/* ==================== SIDEBAR ==================== */}
      <aside className="w-80 shrink-0 glass-panel flex flex-col">

        {/* Logo */}
        <div className="p-6 border-b border-zinc-800/60">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-brand-500 to-brand-700 rounded-xl shadow-lg shadow-brand-600/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-zinc-50 tracking-tight">TenderMind AI</h1>
              <p className="text-[11px] text-zinc-500 font-medium tracking-wide">ENTERPRISE RFP AUTOMATION</p>
            </div>
          </div>
        </div>

        {/* RFP Selector */}
        <div className="p-6 flex-1 overflow-y-auto space-y-5">
          <div>
            <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
              <Search className="w-3 h-3" />
              Data Ingestion
            </h2>

            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Select RFP to Process
            </label>

            {rfps.length === 0 ? (
              <div className="bg-brand-950/30 border border-brand-900/40 text-brand-300 text-sm p-4 rounded-xl">
                <p className="font-medium mb-1">No RFPs found</p>
                <p className="text-xs text-brand-400/60 leading-relaxed">
                  Upload a new RFP to your Google Drive <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-[11px]">/rfp</code> folder.
                </p>
              </div>
            ) : (
              <>
                <div className="relative group">
                  <select
                    value={selectedRfp}
                    onChange={(e) => setSelectedRfp(e.target.value)}
                    className="select-field pr-10"
                    disabled={isBusy}
                  >
                    {rfps.map((rfp) => (
                      <option key={rfp.id} value={rfp.id}>{rfp.name}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none group-focus-within:text-brand-400 transition-colors" />
                </div>

                {selectedRfp && (
                  <div className="mt-3 flex items-center gap-2 bg-emerald-950/25 border border-emerald-900/30 text-emerald-300 text-xs py-2 px-3 rounded-lg">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span className="truncate">
                      <span className="font-semibold">{rfps.find(r => r.id === selectedRfp)?.name}</span>
                      <span className="text-emerald-500/60"> — Ready</span>
                    </span>
                  </div>
                )}
              </>
            )}

            <button
              onClick={fetchRfps}
              disabled={isBusy}
              className="mt-3 text-[11px] text-zinc-500 hover:text-brand-400 disabled:opacity-40 flex items-center gap-1.5 transition-colors font-medium"
            >
              <RefreshCw className="w-3 h-3" /> Refresh list
            </button>
          </div>

          {/* Ingest Button */}
          <button
            onClick={handleIngest}
            disabled={!selectedRfp || isBusy}
            className="btn-primary w-full flex items-center justify-center gap-2.5"
          >
            {isIngesting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
            {isIngesting ? 'Processing…' : 'Ingest & Index'}
          </button>

          <div className="border-t border-zinc-800/50" />

          {/* System Status */}
          <div>
            <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.15em] mb-3 flex items-center gap-2">
              <Shield className="w-3 h-3" />
              System Status
            </h2>
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-500">Indexed RFPs</span>
                <span className="text-zinc-300 font-semibold bg-zinc-800 px-2 py-0.5 rounded-md">{rfps.length}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-500">Model</span>
                <span className="text-zinc-300 font-mono text-[11px]">Gemini 3.5 Flash</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-500">Embeddings</span>
                <span className="text-zinc-300 font-mono text-[11px]">text-embedding-004</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-5 border-t border-zinc-800/60">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[11px] text-zinc-500 font-medium">Backend Connected</span>
          </div>
        </div>
      </aside>

      {/* ==================== MAIN CONTENT ==================== */}
      <main className="flex-1 flex flex-col overflow-hidden">

        {/* Header */}
        <header className="shrink-0 bg-zinc-900/40 backdrop-blur-sm border-b border-zinc-800/50 px-10 py-6">
          <h2 className="text-xl font-semibold text-zinc-50">RFP Analysis Workspace</h2>
          <p className="text-sm text-zinc-500 mt-1">
            Review specifications, assess legal risks, and generate proposals.
          </p>
        </header>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-10 py-8">
          <div className="max-w-[1280px] mx-auto space-y-8">

            <FileUploader onUploadSuccess={fetchRfps} />

            {/* ---- EMPTY STATE ---- */}
            {!hasResults && !isBusy && !selectedRfp && (
              <div className="card flex flex-col items-center justify-center py-20 px-8">
                <div className="p-4 bg-zinc-800 rounded-2xl mb-5">
                  <Inbox className="w-10 h-10 text-zinc-600" />
                </div>
                <h3 className="text-lg font-semibold text-zinc-300 mb-2">No analysis yet</h3>
                <p className="text-sm text-zinc-500 text-center max-w-md leading-relaxed">
                  Select an RFP from the sidebar, click <span className="text-brand-400 font-medium">Ingest & Index</span> to vectorize it, then run a <span className="text-brand-400 font-medium">Pre-Review Analysis</span> to begin.
                </p>
              </div>
            )}

            {/* ---- STEP 1: Analyze ---- */}
            {selectedRfp && !hasResults && !isGenerating && (
              <div className={`card p-8 ${isAnalyzing ? 'loading-pulse' : ''}`}>
                <h3 className="text-[11px] font-bold text-zinc-500 uppercase tracking-[0.15em] mb-6 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-brand-400" />
                  Step 1 — Analyze & Review
                </h3>

                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Focus Area for the Analyst Agent
                </label>
                <input
                  type="text"
                  value={focusArea}
                  onChange={(e) => setFocusArea(e.target.value)}
                  className="input-field mb-6"
                  placeholder="e.g. General requirements and deliverables"
                  disabled={isBusy}
                />

                <button
                  onClick={runPreReview}
                  disabled={isBusy}
                  className="btn-primary flex items-center gap-2.5"
                >
                  {isAnalyzing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  {isAnalyzing ? 'Processing…' : 'Run Pre-Review Analysis'}
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {isBusy && (
              <div className="flex items-center justify-center gap-3 py-8">
                <div className="relative">
                  <div className="w-10 h-10 rounded-full border-2 border-zinc-800" />
                  <div className="absolute inset-0 w-10 h-10 rounded-full border-2 border-transparent border-t-brand-500 animate-spin" />
                </div>
                <span className="text-sm text-zinc-400 font-medium">
                  {isIngesting && 'Extracting & vectorizing document…'}
                  {isAnalyzing && 'Gemini agents are analyzing the RFP…'}
                  {isGenerating && 'Bid Writer is generating proposal…'}
                </span>
              </div>
            )}

            {/* ---- PHASE 1 RESULTS ---- */}
            {analystFindings && strategyAssessment && legalReview && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="card overflow-hidden flex flex-col">
                  <div className="px-6 py-4 border-b border-zinc-800/60 bg-brand-950/20 flex items-center gap-2.5">
                    <Search className="w-4 h-4 text-brand-400" />
                    <h4 className="text-sm font-semibold text-brand-200">Analyst Findings</h4>
                  </div>
                  <div className="p-6 text-sm text-zinc-300 leading-relaxed overflow-y-auto max-h-[450px] prose prose-invert prose-sm max-w-none prose-zinc">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(analystFindings || '')}</ReactMarkdown>
                  </div>
                </div>

                <div className="card overflow-hidden flex flex-col border-blue-900/20">
                  <div className="px-6 py-4 border-b border-zinc-800/60 bg-blue-950/20 flex items-center gap-2.5">
                    <Activity className="w-4 h-4 text-blue-500" />
                    <h4 className="text-sm font-semibold text-blue-200">Strategic Alignment</h4>
                  </div>
                  <div className="p-6 text-sm text-zinc-300 leading-relaxed overflow-y-auto max-h-[450px] prose prose-invert prose-sm max-w-none prose-zinc">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(strategyAssessment || '')}</ReactMarkdown>
                  </div>
                </div>

                <div className="card overflow-hidden flex flex-col border-amber-900/20">
                  <div className="px-6 py-4 border-b border-zinc-800/60 bg-amber-950/20 flex items-center gap-2.5">
                    <Shield className="w-4 h-4 text-amber-500" />
                    <h4 className="text-sm font-semibold text-amber-200">Legal Expert Review</h4>
                  </div>
                  <div className="p-6 text-sm text-zinc-300 leading-relaxed overflow-y-auto max-h-[450px] prose prose-invert prose-sm max-w-none prose-zinc">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(legalReview || '')}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            {/* ---- HITL GUARDRAIL ---- */}
            {awaitingApproval && (
              <div className="relative card overflow-hidden border-amber-700/40">
                <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-amber-400 to-amber-600" />
                <div className="p-8 pl-10">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20">
                      <ShieldAlert className="w-6 h-6 text-amber-500" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-amber-400">Human Validation Required</h3>
                      <p className="text-[11px] text-zinc-500 font-medium tracking-wide">SECURITY GUARDRAIL • HITL PROTOCOL</p>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 mb-7 leading-relaxed max-w-2xl">
                    Please review the Legal Agent's risk assessment above. The Bid Writer Agent is
                    <span className="text-amber-400 font-semibold"> fundamentally blocked </span>
                    from generating a proposal until you explicitly approve the identified risks.
                  </p>
                  <div className="flex gap-3">
                    <button onClick={approveAndGenerate} disabled={isBusy} className="btn-success flex items-center gap-2.5">
                      <CheckCircle className="w-4 h-4" />
                      Approve & Generate Proposal
                    </button>
                    <button onClick={rejectAnalysis} disabled={isBusy} className="btn-danger flex items-center gap-2">
                      Reject / Abort
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ---- FINAL PROPOSAL ---- */}
            {finalProposal && (
              <div className="card overflow-hidden border-emerald-800/30">
                <div className="px-8 py-5 border-b border-zinc-800/60 bg-emerald-950/15 flex items-center gap-3">
                  <div className="p-2.5 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-emerald-400">Final Bid Proposal</h3>
                    <p className="text-[11px] text-zinc-500 font-medium">Generated by Bid Writer Agent • Gemini 3.5 Flash</p>
                  </div>
                </div>
                <div className="p-8 text-sm text-zinc-300 leading-relaxed prose prose-invert prose-sm max-w-none prose-zinc">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(finalProposal || '')}</ReactMarkdown>
                </div>
                <div className="p-6 border-t border-zinc-800/60 bg-emerald-950/10 flex justify-end">
                  <button onClick={resetState} className="btn-primary flex items-center gap-2">
                    <RefreshCw className="w-4 h-4" /> Start New Analysis
                  </button>
                </div>
              </div>
            )}

            <div className="h-8" />
          </div>
        </div>
      </main>
    </div>
  )
}

export default Dashboard
