import { useTranslation } from 'react-i18next';

export function DemoPage() {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">{t('nav.demo')}</h1>
      <div className="card">
        <p className="text-gray-400">
          Demo trading sandbox — practice executions without real capital.
          Connect a demo broker account from the Account page to get started.
        </p>
      </div>
    </div>
  );
}
