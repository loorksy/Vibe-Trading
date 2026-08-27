import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useUiStore } from '@/stores/uiStore';
import { useInstrumentStore } from '@/stores/uiStore';

interface SymbolPickerProps {
  value?: string;
  onChange?: (canonicalId: string) => void;
  className?: string;
  compact?: boolean;
}

export function SymbolPicker({ value, onChange, className = '', compact = false }: SymbolPickerProps) {
  const { t } = useTranslation();
  const selectedSymbol = useUiStore((s) => s.selectedSymbol);
  const setSelectedSymbol = useUiStore((s) => s.setSelectedSymbol);
  const openModal = useUiStore((s) => s.openModal);
  const instruments = useInstrumentStore((s) => s.instruments);
  const loadInstruments = useInstrumentStore((s) => s.loadInstruments);

  const current = value ?? selectedSymbol;
  const display = instruments.find((i) => i.canonical_id === current)?.display_symbol ?? current.replace('_', '/');

  useEffect(() => {
    if (instruments.length === 0) loadInstruments();
  }, [instruments.length, loadInstruments]);

  const handleClick = () => {
    openModal('symbolPicker', {
      onSelect: (id: string) => {
        if (onChange) onChange(id);
        else setSelectedSymbol(id);
      },
    });
  };

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center gap-2 rounded-lg border border-gray-600 bg-surface px-3 py-2 text-sm font-medium text-gray-100 transition-colors hover:border-accent hover:bg-surface-overlay ${compact ? 'py-1.5 text-xs' : ''} ${className}`}
    >
      <svg className="h-4 w-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
      <span className="font-mono">{display}</span>
      <svg className="h-3 w-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
      <span className="sr-only">{t('common.selectSymbol')}</span>
    </button>
  );
}
