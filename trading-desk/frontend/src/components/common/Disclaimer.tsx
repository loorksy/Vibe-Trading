import { useTranslation } from 'react-i18next';

export function Disclaimer() {
  const { t } = useTranslation();

  return (
    <div className="border-t border-gray-700/50 bg-surface px-4 py-2 text-center text-xs text-gray-500">
      {t('disclaimer.text')}
    </div>
  );
}
