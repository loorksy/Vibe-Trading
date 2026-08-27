import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function StrategiesPage() {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t('strategies.title')}</h1>
        <Link to="/strategies/new" className="btn-primary">{t('strategies.new')}</Link>
      </div>
      <p className="text-gray-500">{t('common.noData')}</p>
    </div>
  );
}
