import React, { useState, useEffect } from 'react'
import {
  Activity,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Send,
  RefreshCw,
  Clock,
  User,
  Stethoscope,
  Layers,
  ShieldCheck,
  ChevronRight,
  Sparkles,
  Search,
  UploadCloud,
  FileCheck2,
  Database
} from 'lucide-react'

interface DocumentoAuditoria {
  documento_id: string
  tipo_documento: string
  nivel_prioridade: string
  data: string
  score_confianca_classificacao: number
  justificativa_roteamento: string
  dados_extraidos?: {
    paciente?: { nome?: string; idade?: number; cpf?: string }
    medico_solicitante?: { nome?: string; crm?: string }
    diagnostico_principal?: string
    cid_sugerido?: string
    medicamentos?: Array<{ nome: string; dosagem?: string; frequencia?: string }>
    observacoes_clinicas?: string
  }
}

interface ItemHistorico {
  data: string
  documento_id: string
  status: string
  nivel_prioridade: string
  destino_principal: string
  bucket: string
}

export default function App() {
  const [abaAtiva, setAbaAtiva] = useState<'auditoria' | 'envio' | 'historico'>('auditoria')
  const [pendentes, setPendentes] = useState<DocumentoAuditoria[]>([])
  const [historico, setHistorico] = useState<ItemHistorico[]>([])
  const [casoSelecionado, setCasoSelecionado] = useState<DocumentoAuditoria | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [mensagemStatus, setMensagemStatus] = useState<{ tipo: 'sucesso' | 'erro'; texto: string } | null>(null)

  // Campos do formulário de decisão
  const [destinoDecisao, setDestinoDecisao] = useState<'rotina' | 'urgente' | 'rejeitado'>('rotina')
  const [revisorNome, setRevisorNome] = useState('Dra. Lethicia')
  const [justificativaDecisao, setJustificativaDecisao] = useState('')
  const [enviandoDecisao, setEnviandoDecisao] = useState(false)

  // Campos de envio de triagem
  const [docIdEnvio, setDocIdEnvio] = useState(() => `DOC-${Math.random().toString(36).substring(2, 9).toUpperCase()}`)
  const [canalOrigem, setCanalOrigem] = useState('Ambulatorio')
  const [textoEnvio, setTextoEnvio] = useState('')
  const [resultadoTriagem, setResultadoTriagem] = useState<any>(null)
  const [processandoTriagem, setProcessandoTriagem] = useState(false)

  const carregarDados = async () => {
    setCarregando(true)
    try {
      const [resPendentes, resHistorico] = await Promise.all([
        fetch('/api/v1/auditoria/pendentes').then(r => (r.ok ? r.json() : [])),
        fetch('/api/v1/documentos').then(r => (r.ok ? r.json() : []))
      ])
      setPendentes(resPendentes)
      setHistorico(resHistorico)
      if (resPendentes.length > 0 && !casoSelecionado) {
        setCasoSelecionado(resPendentes[0])
      } else if (resPendentes.length > 0 && casoSelecionado) {
        const atualizado = resPendentes.find((p: any) => p.documento_id === casoSelecionado.documento_id)
        setCasoSelecionado(atualizado || resPendentes[0])
      } else {
        setCasoSelecionado(null)
      }
    } catch (err) {
      console.error('Erro ao carregar dados:', err)
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarDados()
  }, [])

  const submeterDecisao = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!casoSelecionado) return
    if (!revisorNome.trim()) {
      setMensagemStatus({ tipo: 'erro', texto: 'Informe o nome do auditor responsável.' })
      return
    }
    if (justificativaDecisao.trim().length < 5) {
      setMensagemStatus({ tipo: 'erro', texto: 'A justificativa precisa ter pelo menos 5 caracteres.' })
      return
    }

    setEnviandoDecisao(true)
    setMensagemStatus(null)

    try {
      const res = await fetch(`/api/v1/auditoria/${casoSelecionado.documento_id}/decisao`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destino: destinoDecisao,
          revisor: revisorNome.trim(),
          justificativa: justificativaDecisao.trim()
        })
      })

      if (!res.ok) {
        const erroJson = await res.json().catch(() => ({}))
        throw new Error(erroJson.detail || 'Falha ao registrar auditoria.')
      }

      setMensagemStatus({
        tipo: 'sucesso',
        texto: `Documento ${casoSelecionado.documento_id} auditado com sucesso e roteado para ${destinoDecisao.toUpperCase()}!`
      })
      setJustificativaDecisao('')
      await carregarDados()
    } catch (err: any) {
      setMensagemStatus({ tipo: 'erro', texto: err.message || 'Erro ao comunicar com a API.' })
    } finally {
      setEnviandoDecisao(false)
    }
  }

  const enviarNovaTriagem = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!textoEnvio.trim()) {
      setMensagemStatus({ tipo: 'erro', texto: 'Insira o texto clínico para processar.' })
      return
    }

    setProcessandoTriagem(true)
    setResultadoTriagem(null)
    setMensagemStatus(null)

    try {
      const res = await fetch('/api/v1/triagem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documento_id: docIdEnvio,
          canal_origem: canalOrigem,
          tipo_arquivo: 'TXT',
          documento_texto: textoEnvio
        })
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || 'Falha na triagem.')
      }

      const dados = await res.json()
      setResultadoTriagem(dados)
      setMensagemStatus({ tipo: 'sucesso', texto: `Triagem processada com sucesso via LangGraph + OCI!` })
      setDocIdEnvio(`DOC-${Math.random().toString(36).substring(2, 9).toUpperCase()}`)
      setTextoEnvio('')
      await carregarDados()
    } catch (err: any) {
      setMensagemStatus({ tipo: 'erro', texto: err.message || 'Erro no envio da triagem.' })
    } finally {
      setProcessandoTriagem(false)
    }
  }

  // Contadores
  const totalDocs = historico.length
  const totalPendentes = pendentes.length
  const totalEmergencias = historico.filter(h => h.destino_principal === 'Fila_Emergencia_Medica').length
  const totalRotina = historico.filter(h => ['Farmacia_Hospitalar', 'Auditoria_Autorizacoes', 'Prontuario_Eletronico_do_Paciente'].includes(h.destino_principal)).length
  const totalRejeitados = historico.filter(h => h.status === 'rejeitado').length

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">MediFlow</h1>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono font-medium">
                  v2.2 React
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Sistema Autônomo de Triagem, Extração e Roteamento Clínico | OCI Always Free
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              OCI Compute Ativa
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-sky-950/60 border border-sky-800/80 text-sky-400 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              Gemini 3.5 Flash-Lite
            </div>
            <button
              onClick={carregarDados}
              disabled={carregando}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
              title="Recarregar dados"
            >
              <RefreshCw className={`w-4 h-4 ${carregando ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6 w-full flex-1 flex flex-col gap-6">
        {/* Metric Cards (KPIs) */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 border-t-4 border-t-sky-500 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <span>Total Documentos</span>
              <FileText className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-2xl font-bold text-white">{totalDocs}</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 border-t-4 border-t-amber-500 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <span>Revisão Humana</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-amber-400">{totalPendentes}</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 border-t-4 border-t-rose-500 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <span>Emergências</span>
              <Activity className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold text-rose-400">{totalEmergencias}</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 border-t-4 border-t-emerald-500 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <span>Rotina</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400">{totalRotina}</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 border-t-4 border-t-slate-500 shadow-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <span>Rejeitados</span>
              <XCircle className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-300">{totalRejeitados}</div>
          </div>
        </div>

        {/* Global Feedback Banner */}
        {mensagemStatus && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between text-sm ${
              mensagemStatus.tipo === 'sucesso'
                ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/40 border-rose-800 text-rose-300'
            }`}
          >
            <div className="flex items-center gap-3">
              {mensagemStatus.tipo === 'sucesso' ? (
                <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
              )}
              <span>{mensagemStatus.texto}</span>
            </div>
            <button
              onClick={() => setMensagemStatus(null)}
              className="text-xs uppercase font-bold tracking-wider hover:opacity-80"
            >
              Fechar
            </button>
          </div>
        )}

        {/* Tabs Navigation */}
        <div className="border-b border-slate-800 flex gap-2">
          <button
            onClick={() => setAbaAtiva('auditoria')}
            className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              abaAtiva === 'auditoria'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            Fila de Auditoria Clínica
            {pendentes.length > 0 && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {pendentes.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setAbaAtiva('envio')}
            className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              abaAtiva === 'envio'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Send className="w-4 h-4" />
            Envio e Triagem de Documentos
          </button>

          <button
            onClick={() => setAbaAtiva('historico')}
            className={`pb-3 px-4 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              abaAtiva === 'historico'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            Histórico & Buckets OCI
          </button>
        </div>

        {/* TAB 1: AUDITORIA CLÍNICA (MASTER-DETAIL VIEW) */}
        {abaAtiva === 'auditoria' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
            {/* Master: Lista de Casos Pendentes */}
            <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 h-fit max-h-[750px] overflow-y-auto">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Casos Retidos ({pendentes.length})
                </span>
                <span className="text-xs text-slate-500">Human-in-the-Loop</span>
              </div>

              {pendentes.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-emerald-500/40" />
                  <p className="text-sm font-medium">Nenhum caso retido na fila!</p>
                  <p className="text-xs text-slate-600 mt-1">Todos os documentos foram roteados automaticamente.</p>
                </div>
              ) : (
                pendentes.map(doc => {
                  const isSelected = casoSelecionado?.documento_id === doc.documento_id
                  return (
                    <div
                      key={doc.documento_id}
                      onClick={() => setCasoSelecionado(doc)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-sky-950/40 border-sky-500/60 shadow-lg shadow-sky-950/20'
                          : 'bg-slate-900/80 border-slate-800/80 hover:bg-slate-800/50 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-mono font-bold text-sky-400">{doc.documento_id}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            doc.nivel_prioridade === 'Urgência Crítica'
                              ? 'bg-rose-950/60 border-rose-800 text-rose-300'
                              : 'bg-amber-950/60 border-amber-800 text-amber-300'
                          }`}
                        >
                          {doc.nivel_prioridade}
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-slate-200 mb-1">{doc.tipo_documento}</div>
                      <div className="flex items-center justify-between text-xs text-slate-400">
                        <span className="truncate max-w-[170px]">
                          {doc.dados_extraidos?.paciente?.nome || 'Paciente não ident.'}
                        </span>
                        <span className="font-mono text-[11px] text-slate-500">
                          Score: {(doc.score_confianca_classificacao * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {/* Detail: Dossiê Clínico + Formulário de Decisão */}
            <div className="lg:col-span-8 flex flex-col gap-6">
              {casoSelecionado ? (
                <>
                  {/* Card Dossiê Clínico */}
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800 mb-5">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                          Dossiê de Revisão Clínica
                        </div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2 mt-0.5">
                          <span className="font-mono text-sky-400">{casoSelecionado.documento_id}</span>
                          <span className="text-slate-400">—</span>
                          <span>{casoSelecionado.tipo_documento}</span>
                        </h2>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          Entrada: {new Date(casoSelecionado.data).toLocaleString('pt-BR')}
                        </span>
                      </div>
                    </div>

                    {/* Alerta de Retenção */}
                    <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/60 text-amber-300 mb-5">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-400 mt-0.5" />
                        <div>
                          <div className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-0.5">
                            Motivo da Retenção para Auditoria
                          </div>
                          <p className="text-sm leading-relaxed text-amber-200">
                            {casoSelecionado.justificativa_roteamento}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t border-amber-900/50 flex items-center justify-between text-xs">
                        <span className="text-amber-400/80">Score de Confiança da Extração IA:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-rose-500 to-amber-500 rounded-full"
                              style={{ width: `${casoSelecionado.score_confianca_classificacao * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-mono font-bold text-amber-300">
                            {(casoSelecionado.score_confianca_classificacao * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Dados Extraídos (Read-Only Grid) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                          <User className="w-3.5 h-3.5 text-sky-400" />
                          Paciente
                        </div>
                        <div className="text-sm font-semibold text-white">
                          {casoSelecionado.dados_extraidos?.paciente?.nome || 'Nome não identificado ou ilegível'}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          Idade: {casoSelecionado.dados_extraidos?.paciente?.idade || 'Não informada'}
                        </div>
                      </div>

                      <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                          <Stethoscope className="w-3.5 h-3.5 text-emerald-400" />
                          Médico Solicitante
                        </div>
                        <div className="text-sm font-semibold text-white">
                          {casoSelecionado.dados_extraidos?.medico_solicitante?.nome || 'Médico não identificado'}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          CRM: {casoSelecionado.dados_extraidos?.medico_solicitante?.crm || 'Ausente ou ilegível'}
                        </div>
                      </div>

                      <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 md:col-span-2">
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                          Diagnóstico & CID-10
                        </div>
                        <div className="text-sm font-semibold text-slate-200">
                          {casoSelecionado.dados_extraidos?.diagnostico_principal || 'Sem diagnóstico textual legível'}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          CID Sugerido:{' '}
                          <span className="font-mono font-semibold text-sky-400">
                            {casoSelecionado.dados_extraidos?.cid_sugerido || 'Nenhum'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Card do Formulário de Ação do Auditor */}
                  <form onSubmit={submeterDecisao} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col gap-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <span className="text-sm font-bold uppercase tracking-wider text-slate-300">
                        Decisão da Auditoria Médica
                      </span>
                      <span className="text-xs text-slate-500">Mover para bucket OCI de destino</span>
                    </div>

                    {/* Segmented Controls para Destino */}
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                        Encaminhar Documento Para:
                      </label>
                      <div className="grid grid-cols-3 gap-3 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
                        <button
                          type="button"
                          onClick={() => setDestinoDecisao('rotina')}
                          className={`py-2.5 px-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                            destinoDecisao === 'rotina'
                              ? 'bg-emerald-600 text-white shadow-md'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                          }`}
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          Rotina
                        </button>

                        <button
                          type="button"
                          onClick={() => setDestinoDecisao('urgente')}
                          className={`py-2.5 px-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                            destinoDecisao === 'urgente'
                              ? 'bg-rose-600 text-white shadow-md'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                          }`}
                        >
                          <AlertTriangle className="w-4 h-4" />
                          Urgente
                        </button>

                        <button
                          type="button"
                          onClick={() => setDestinoDecisao('rejeitado')}
                          className={`py-2.5 px-3 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                            destinoDecisao === 'rejeitado'
                              ? 'bg-slate-700 text-white shadow-md'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                          }`}
                        >
                          <XCircle className="w-4 h-4" />
                          Rejeitar
                        </button>
                      </div>
                    </div>

                    {/* Revisor e Justificativa */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                          Nome do Revisor Responsável
                        </label>
                        <input
                          type="text"
                          value={revisorNome}
                          onChange={e => setRevisorNome(e.target.value)}
                          placeholder="Ex: Dra. Lethicia"
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                          Justificativa Clínica da Decisão
                        </label>
                        <input
                          type="text"
                          value={justificativaDecisao}
                          onChange={e => setJustificativaDecisao(e.target.value)}
                          placeholder="Ex: Dados conferidos com prontuário e CRM validado."
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={enviandoDecisao}
                      className="w-full mt-2 py-3 px-4 rounded-xl font-bold bg-gradient-to-r from-sky-600 to-blue-700 hover:from-sky-500 hover:to-blue-600 text-white shadow-lg shadow-sky-900/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <FileCheck2 className="w-5 h-5" />
                      {enviandoDecisao ? 'Registrando Decisão...' : 'Registrar Decisão no Armazenamento OCI'}
                    </button>
                  </form>
                </>
              ) : (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
                  <p>Selecione um caso na coluna ao lado para iniciar a auditoria.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: ENVIO E TRIAGEM */}
        {abaAtiva === 'envio' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-bold text-white mb-1">Enviar Documento para Triagem Automática</h2>
              <p className="text-xs text-slate-400 mb-5">
                Processamento multimodal com classificação, extração e validação determinística.
              </p>

              <form onSubmit={enviarNovaTriagem} className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                      ID do Documento
                    </label>
                    <input
                      type="text"
                      value={docIdEnvio}
                      onChange={e => setDocIdEnvio(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-sky-400 font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                      Canal de Origem
                    </label>
                    <select
                      value={canalOrigem}
                      onChange={e => setCanalOrigem(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none"
                    >
                      <option value="Ambulatorio">Ambulatório</option>
                      <option value="Pronto_Socorro">Pronto Socorro</option>
                      <option value="Internacao">Internação</option>
                      <option value="Recepcao">Recepção</option>
                      <option value="Auditoria">Auditoria</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Conteúdo do Documento Clínico (Texto ou Laudo)
                  </label>
                  <textarea
                    rows={8}
                    value={textoEnvio}
                    onChange={e => setTextoEnvio(e.target.value)}
                    placeholder="Cole o texto do laudo, prescrição ou guia médica..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white font-mono focus:outline-none focus:border-sky-500"
                  ></textarea>
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      setTextoEnvio(
                        'HOSPITAL GERAL. Paciente: Pedro Henrique Ramos, 52 anos. Prescrição: Enoxaparina 40mg SC 1x ao dia por 7 dias. Médico: Dr. Alexandre Toledo CRM 78945/SP. Diagnóstico: Prevenção de TEV no pós-operatório.'
                      )
                    }
                    className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                  >
                    Exemplo Rotina
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setTextoEnvio(
                        'URGENCIA MEDICA. Paciente: Luciana Castro, 45 anos. Angiotomografia de Torax: Falha de enchimento em arteria pulmonar principal direita compativel com Tromboembolismo Pulmonar Agudo Macico (TEP). Sinais de sobrecarga de ventriculo direito. Medico Plantonista: Dr. Sergio Mendes CRM 88214/SP.'
                      )
                    }
                    className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                  >
                    Exemplo Emergência (TEP)
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={processandoTriagem}
                  className="w-full py-3 px-4 rounded-xl font-bold bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-900/30 transition flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
                >
                  <Send className="w-4 h-4" />
                  {processandoTriagem ? 'Processando Grafo...' : 'Executar Triagem Automática'}
                </button>
              </form>
            </div>

            {/* Resultado da Triagem */}
            <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-bold text-white mb-1">Resultado da Análise IA</h2>
              <p className="text-xs text-slate-400 mb-5">Retorno detalhado dos nós de classificação e roteamento.</p>

              {resultadoTriagem ? (
                <div className="flex flex-col gap-4">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-slate-400">STATUS DA TRIAGEM</div>
                      <div className="text-base font-bold text-emerald-400">{resultadoTriagem.status}</div>
                    </div>
                    <div>
                      <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-sky-950 text-sky-400 border border-sky-800">
                        {resultadoTriagem.classificacao?.nivel_prioridade}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-500 block mb-1">Tipo de Documento:</span>
                      <span className="font-semibold text-slate-200">{resultadoTriagem.classificacao?.tipo_documento}</span>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-500 block mb-1">Destino Principal:</span>
                      <span className="font-semibold text-sky-400">{resultadoTriagem.decisao_roteamento?.destino_principal}</span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-500 block mb-1">Justificativa do Roteamento:</span>
                    <p className="text-slate-300 leading-relaxed">
                      {resultadoTriagem.decisao_roteamento?.justificativa_roteamento}
                    </p>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-500 block mb-1">Bucket OCI Always Free:</span>
                    <span className="font-mono text-emerald-400">{resultadoTriagem.armazenamento_oci?.bucket}</span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-slate-500">
                  <UploadCloud className="w-12 h-12 mx-auto mb-2 text-slate-700" />
                  <p className="text-sm">Envie um documento para ver o resultado do LangGraph aqui.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: HISTÓRICO & BUCKETS OCI */}
        {abaAtiva === 'historico' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col gap-5">
            <div>
              <h2 className="text-lg font-bold text-white mb-1">Histórico de Documentos no Armazenamento OCI</h2>
              <p className="text-xs text-slate-400">
                Visualização consolidada dos 5 buckets segregados no Oracle Cloud Infrastructure.
              </p>
            </div>

            {/* Badges dos 5 Buckets */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <span className="font-mono text-slate-400 block font-semibold">mediflow-recebidos</span>
                <span className="text-[11px] text-slate-500">Quarentena / Ingestão</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-emerald-900/60 text-xs">
                <span className="font-mono text-emerald-400 block font-semibold">mediflow-rotina</span>
                <span className="text-[11px] text-slate-500">Farmácia, PEP e Autoriz.</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-rose-900/60 text-xs">
                <span className="font-mono text-rose-400 block font-semibold">mediflow-urgentes</span>
                <span className="text-[11px] text-slate-500">Emergência Médica</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-amber-900/60 text-xs">
                <span className="font-mono text-amber-400 block font-semibold">mediflow-auditoria</span>
                <span className="text-[11px] text-slate-500">Revisão Humana</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <span className="font-mono text-slate-400 block font-semibold">mediflow-rejeitados</span>
                <span className="text-[11px] text-slate-500">Falhas e Inconsistências</span>
              </div>
            </div>

            {/* Tabela de Histórico */}
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950 text-slate-400 text-xs uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Data</th>
                    <th className="py-3 px-4">Documento</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Prioridade</th>
                    <th className="py-3 px-4">Destino Principal</th>
                    <th className="py-3 px-4">Bucket OCI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200">
                  {historico.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-slate-500">
                        Nenhum documento gravado ainda.
                      </td>
                    </tr>
                  ) : (
                    historico.map(h => (
                      <tr key={h.documento_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 text-xs font-mono text-slate-400">
                          {new Date(h.data).toLocaleString('pt-BR')}
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-sky-400">{h.documento_id}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                              h.status === 'rejeitado'
                                ? 'bg-rose-950/60 text-rose-400 border border-rose-800'
                                : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                            }`}
                          >
                            {h.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs">{h.nivel_prioridade}</td>
                        <td className="py-3 px-4 text-xs font-medium text-slate-300">{h.destino_principal}</td>
                        <td className="py-3 px-4 text-xs font-mono text-emerald-400/90">{h.bucket}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/40 py-4 px-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong className="text-slate-300">MediFlow</strong> · Hackathon ONE G10 (Grupo 10)
          </div>
          <div>
            Equipe: André · Ingrid · Guilherme · Lethicia | Infra: OCI VM Always Free & Object Storage
          </div>
        </div>
      </footer>
    </div>
  )
}
