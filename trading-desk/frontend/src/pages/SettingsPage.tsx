import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '@/stores/settingsStore';
import type { OperatorSettings } from '@/types';

export function SettingsPage() {
  const { t } = useTranslation();
  const { settings, loadSettings, updateSettings, theme, setTheme } = useSettingsStore();
  const [form, setForm] = useState<Partial<OperatorSettings>>({});

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    if (settings) setForm(settings);
  }, [settings]);

  const handleSave = async () => {
    await updateSettings({
      risk_per_trade_r: form.risk_per_trade_r,
      spread_limit_pips: form.spread_limit_pips,
      daily_loss_limit_r: form.daily_loss_limit_r,
      consecutive_loss_limit: form.consecutive_loss_limit,
      exposure_cap_r: form.exposure_cap_r,
    });
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold">{t('settings.title')}</h1>

      <div className="card mb-4 space-y-4">
        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('settings.theme')}</label>
          <div className="flex gap-2">
            <button
              onClick={() => setTheme('dark')}
              className={`btn ${theme === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
            >
              {t('settings.dark')}
            </button>
            <button
              onClick={() => setTheme('light')}
              className={`btn ${theme === 'light' ? 'btn-primary' : 'btn-secondary'}`}
            >
              {t('settings.light')}
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('settings.risk')}</label>
          <input
            className="input"
            type="number"
            step="0.1"
            value={form.risk_per_trade_r ?? ''}
            onChange={(e) => setForm({ ...form, risk_per_trade_r: parseFloat(e.target.value) })}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-gray-400">{t('settings.spreadLimit')}</label>
          <input
            className="input"
            type="number"
            step="0.1"
            value={form.spread_limit_pips ?? ''}
            onChange={(e) => setForm({ ...form, spread_limit_pips: parseFloat(e.target.value) })}
          />
        </div>

        <button onClick={handleSave} className="btn-primary">{t('common.save')}</button>
      </div>
    </div>
  );
}
