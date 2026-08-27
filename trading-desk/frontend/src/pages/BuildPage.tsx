import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function BuildPage() {
  const { t } = useTranslation();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-2 text-2xl font-bold">{t('build.title')}</h1>
      <p className="mb-6 text-gray-500">{t('build.subtitle')}</p>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">{t('build.newStrategy')}</h2>
          <div className="space-y-3">
            <input className="input" placeholder="Strategy name" value={name} onChange={(e) => setName(e.target.value)} />
            <textarea className="input min-h-[100px]" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
            <Link to="/strategies/new" className="btn-primary inline-flex">{t('build.newStrategy')}</Link>
          </div>
        </div>

        <div className="card">
          <h2 className="mb-4 text-lg font-semibold">{t('build.runBacktest')}</h2>
          <p className="mb-4 text-sm text-gray-500">Select a strategy version and run a backtest against historical data.</p>
          <Link to="/strategies" className="btn-secondary inline-flex">{t('nav.strategies')}</Link>
        </div>
      </div>
    </div>
  );
}
