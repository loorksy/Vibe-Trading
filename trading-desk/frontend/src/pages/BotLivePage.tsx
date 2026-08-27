import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/client';

export function BotLivePage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const [confirmation, setConfirmation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePromote = async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      await api.promoteLive(id, confirmation);
      navigate(`/bots/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-6 text-2xl font-bold">{t('bots.promoteLive')}</h1>
      <div className="card space-y-4">
        <p className="text-sm text-warning">
          Promoting to live trading involves real capital. Confirm by entering the bot symbol.
        </p>
        {error && <p className="text-sm text-danger">{error}</p>}
        <input
          className="input"
          placeholder="Confirmation symbol (e.g. EUR_USD)"
          value={confirmation}
          onChange={(e) => setConfirmation(e.target.value)}
        />
        <div className="flex gap-2">
          <button onClick={handlePromote} disabled={loading || !confirmation} className="btn-danger">
            {loading ? t('common.loading') : t('bots.promoteLive')}
          </button>
          <button onClick={() => navigate(`/bots/${id}`)} className="btn-secondary">{t('common.cancel')}</button>
        </div>
      </div>
    </div>
  );
}
