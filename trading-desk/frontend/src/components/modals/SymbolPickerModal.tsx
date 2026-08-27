import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '@/components/common/Modal';
import { useUiStore, useInstrumentStore } from '@/stores/uiStore';

export function SymbolPickerModal() {
  const { t } = useTranslation();
  const { activeModal, closeModal, modalData } = useUiStore();
  const instruments = useInstrumentStore((s) => s.instruments);
  const loadInstruments = useInstrumentStore((s) => s.loadInstruments);
  const loading = useInstrumentStore((s) => s.loading);
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (activeModal === 'symbolPicker') {
      loadInstruments(query);
    }
  }, [activeModal, query, loadInstruments]);

  const handleSelect = (canonicalId: string) => {
    const onSelect = modalData.onSelect as ((id: string) => void) | undefined;
    onSelect?.(canonicalId);
    closeModal();
    setQuery('');
  };

  return (
    <Modal
      open={activeModal === 'symbolPicker'}
      onClose={() => { closeModal(); setQuery(''); }}
      title={t('modals.symbolPicker.title')}
      size="lg"
    >
      <div className="mb-4">
        <input
          className="input"
          placeholder={t('modals.symbolPicker.search')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
      </div>
      <div className="max-h-80 overflow-y-auto">
        {loading ? (
          <p className="py-8 text-center text-gray-500">{t('common.loading')}</p>
        ) : instruments.length === 0 ? (
          <p className="py-8 text-center text-gray-500">{t('common.noData')}</p>
        ) : (
          <div className="grid gap-1">
            {instruments.map((inst) => (
              <button
                key={inst.canonical_id}
                onClick={() => handleSelect(inst.canonical_id)}
                className="flex items-center justify-between rounded-lg px-3 py-2.5 text-start hover:bg-surface-overlay"
              >
                <div>
                  <span className="font-mono font-medium">{inst.display_symbol}</span>
                  <span className="ms-2 text-xs text-gray-500">{inst.asset_class}</span>
                </div>
                {!inst.tradable && (
                  <span className="text-xs text-gray-600">N/A</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}
