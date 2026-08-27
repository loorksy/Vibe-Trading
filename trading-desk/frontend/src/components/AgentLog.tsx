import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';
import { useChatStore } from '@/stores/uiStore';
import type { AgentLogEntry } from '@/types';

export function AgentLog() {
  const { t } = useTranslation();
  const sessionId = useChatStore((s) => s.sessionId);
  const [open, setOpen] = useState(false);
  const [log, setLog] = useState<AgentLogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && sessionId) {
      setLoading(true);
      api
        .agentLog(sessionId)
        .then((res) => setLog(res.transcript || []))
        .catch(() => setLog([]))
        .finally(() => setLoading(false));
    }
  }, [open, sessionId]);

  if (!sessionId) return null;

  return (
    <div className="border-t border-gray-700">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2 text-sm text-gray-400 hover:bg-surface-overlay"
      >
        <span className="flex items-center gap-2">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          {t('ask.agentLog')}
        </span>
        <svg
          className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="max-h-48 overflow-y-auto bg-surface px-4 py-2 font-mono text-xs text-gray-400">
          {loading ? (
            <p>{t('common.loading')}</p>
          ) : log.length === 0 ? (
            <p>{t('common.noData')}</p>
          ) : (
            log.map((entry, i) => (
              <div key={i} className="mb-2 border-b border-gray-800 pb-2 last:border-0">
                <pre className="whitespace-pre-wrap break-words">
                  {typeof entry === 'string' ? entry : JSON.stringify(entry, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
