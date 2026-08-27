import { useState } from 'react';
import { ArtifactRenderer } from '@/components/artifacts/ArtifactRenderer';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import { useChatStore } from '@/stores/uiStore';
import { useUiStore } from '@/stores/uiStore';
import { SymbolPicker } from '@/components/SymbolPicker';
import { AgentLog } from '@/components/AgentLog';
import type { AnalysisMode } from '@/types';

const TIMEFRAMES = ['15m', '1h', '4h', '1d'];

export function AskPage() {
  const { t } = useTranslation();
  const selectedSymbol = useUiStore((s) => s.selectedSymbol);
  const {
    sessionId, messages, mode, timeframe, loading,
    setSessionId, addMessage, setMode, setTimeframe, setLoading, reset,
  } = useChatStore();
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: userMsg,
      analysis_mode: mode,
      created_at: new Date().toISOString(),
    });
    setLoading(true);
    try {
      const res = await api.sendMessage({
        session_id: sessionId || undefined,
        message: userMsg,
        mode,
        canonical_id: selectedSymbol,
        timeframe,
      });
      setSessionId(res.session_id);
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.message,
        artifacts: res.artifacts,
        analysis_mode: mode,
        created_at: new Date().toISOString(),
      });
    } catch {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: t('common.error'),
        created_at: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-10rem)] max-w-4xl flex-col">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t('ask.title')}</h1>
        <div className="flex items-center gap-2">
          <button onClick={reset} className="btn-ghost text-sm">{t('ask.newChat')}</button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-3">
        <SymbolPicker />
        <select className="input w-auto" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
          {TIMEFRAMES.map((tf) => <option key={tf} value={tf}>{tf}</option>)}
        </select>
        <div className="flex rounded-lg bg-surface-overlay p-1">
          {(['quick_scan', 'deep_analysis'] as AnalysisMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                mode === m ? 'bg-accent text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {m === 'quick_scan' ? t('ask.quickScan') : t('ask.deepAnalysis')}
            </button>
          ))}
        </div>
      </div>

      <div className="card flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 && (
          <p className="py-12 text-center text-gray-500">{t('ask.placeholder')}</p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-4 py-3 ${
              msg.role === 'user' ? 'bg-accent text-white' : 'bg-surface-overlay'
            }`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.artifacts && <ArtifactRenderer artifacts={msg.artifacts} />}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-xl bg-surface-overlay px-4 py-3">
              <div className="flex gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-gray-500" style={{ animationDelay: '0ms' }} />
                <span className="h-2 w-2 animate-bounce rounded-full bg-gray-500" style={{ animationDelay: '150ms' }} />
                <span className="h-2 w-2 animate-bounce rounded-full bg-gray-500" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <AgentLog />

      <div className="mt-3 flex gap-2">
        <input
          className="input flex-1"
          placeholder={t('ask.placeholder')}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary">
          {t('ask.send')}
        </button>
      </div>
    </div>
  );
}
