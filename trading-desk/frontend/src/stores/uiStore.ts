import { create } from 'zustand';
import type { AnalysisMode, ChatMessage, Instrument } from '@/types';

type ModalType =
  | 'connectBroker'
  | 'symbolPicker'
  | 'executeTrade'
  | 'emergencyKill'
  | null;

interface UiState {
  activeModal: ModalType;
  modalData: Record<string, unknown>;
  selectedSymbol: string;
  sidebarOpen: boolean;
  agentLogOpen: boolean;
  openModal: (modal: ModalType, data?: Record<string, unknown>) => void;
  closeModal: () => void;
  setSelectedSymbol: (symbol: string) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleAgentLog: () => void;
  setAgentLogOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeModal: null,
  modalData: {},
  selectedSymbol: 'EUR_USD',
  sidebarOpen: false,
  agentLogOpen: false,

  openModal: (modal, data = {}) => set({ activeModal: modal, modalData: data }),
  closeModal: () => set({ activeModal: null, modalData: {} }),
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleAgentLog: () => set((s) => ({ agentLogOpen: !s.agentLogOpen })),
  setAgentLogOpen: (open) => set({ agentLogOpen: open }),
}));

interface ChatState {
  sessionId: string | null;
  messages: ChatMessage[];
  mode: AnalysisMode;
  timeframe: string;
  loading: boolean;
  setSessionId: (id: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setMode: (mode: AnalysisMode) => void;
  setTimeframe: (tf: string) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  mode: 'quick_scan',
  timeframe: '1h',
  loading: false,

  setSessionId: (sessionId) => set({ sessionId }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  setMode: (mode) => set({ mode }),
  setTimeframe: (timeframe) => set({ timeframe }),
  setLoading: (loading) => set({ loading }),
  reset: () => set({ sessionId: null, messages: [], loading: false }),
}));

interface InstrumentState {
  instruments: Instrument[];
  loading: boolean;
  loadInstruments: (q?: string) => Promise<void>;
}

export const useInstrumentStore = create<InstrumentState>((set) => ({
  instruments: [],
  loading: false,

  loadInstruments: async (q = '') => {
    set({ loading: true });
    try {
      const instruments = await import('@/api/client').then((m) => m.api.instruments(q));
      set({ instruments });
    } catch {
      set({ instruments: [] });
    } finally {
      set({ loading: false });
    }
  },
}));
