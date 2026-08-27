import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function StrategyVersionsPage() {
  const { t } = useTranslation();
  const { id } = useParams();

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('strategies.versions')}</h1>
      <p className="mb-4 text-sm text-gray-500">Strategy ID: {id}</p>
      <div className="card">
        <p className="text-gray-500">{t('common.noData')}</p>
        <Link to={`/strategies/${id}/optimize`} className="btn-secondary mt-4 inline-flex">
          {t('strategies.optimize')}
        </Link>
      </div>
    </div>
  );
}
