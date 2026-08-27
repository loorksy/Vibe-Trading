import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import tr from './tr.json';
import ar from './ar.json';

const savedLang = localStorage.getItem('trading-desk-settings');
let defaultLang = 'en';
try {
  if (savedLang) {
    const parsed = JSON.parse(savedLang);
    defaultLang = parsed?.state?.language || 'en';
  }
} catch {
  // ignore
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    tr: { translation: tr },
    ar: { translation: ar },
  },
  lng: defaultLang,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

document.documentElement.dir = defaultLang === 'ar' ? 'rtl' : 'ltr';
document.documentElement.lang = defaultLang;

export default i18n;
