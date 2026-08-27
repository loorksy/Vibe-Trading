import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function StrategyNewPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [code, setCode] = useState('# Strategy code\n');

  const handleSave = () => {
    // Placeholder — backend strategy CRUD not yet exposed
    navigate('/strategies');
  };

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('strategies.new')}</h1>
      <div className="card space-y-4">
        <input className="input" placeholder="Strategy name" value={name} onChange={(e) => setName(e.target.value)} />
        <textarea className="input min-h-[300px] font-mono text-sm" value={code} onChange={(e) => setCode(e.target.value)} />
        <div className="flex gap-2">
          <button onClick={handleSave} className="btn-primary">{t('common.save')}</button>
          <button onClick={() => navigate('/strategies')} className="btn-secondary">{t('common.cancel')}</button>
        </div>
      </div>
    </div>
  );
}
