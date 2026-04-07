import AsyncStorage from '@react-native-async-storage/async-storage';
import { I18nManager } from 'react-native';

export type Language = 'en' | 'ur';

const LANGUAGE_KEY = 'app_language';

const translations = {
  en: {
    appName: 'EduPilot',
    signIn: 'Sign In',
    signOut: 'Sign Out',
    loading: 'Loading...',
    dashboard: 'Dashboard',
    myCourses: 'My Courses',
    upcomingAssignments: 'Upcoming Assignments',
    noCoursesFound: 'No courses found.',
    noAssignments: 'No upcoming assignments',
    askAI: 'Ask AI',
    queryPlaceholder: 'Ask about your courses...',
    submit: 'Submit',
    voice: 'Voice',
    lectures: 'Lectures',
    settings: 'Settings',
    lmsCredentials: 'LMS Credentials',
    email: 'Email',
    password: 'Password',
    save: 'Save',
    syncNow: 'Sync Now',
    lastSync: 'Last Sync',
    offline: 'You are offline',
  },
  ur: {
    appName: 'ایڈوپائلٹ',
    signIn: 'سائن ان کریں',
    signOut: 'سائن آؤٹ',
    loading: 'لوڈ ہو رہا ہے...',
    dashboard: 'ڈیش بورڈ',
    myCourses: 'میرے کورسز',
    upcomingAssignments: 'آنے والے اسائنمنٹس',
    noCoursesFound: 'کوئی کورس نہیں ملا۔',
    noAssignments: 'کوئی آنے والا اسائنمنٹ نہیں',
    askAI: 'AI سے پوچھیں',
    queryPlaceholder: 'اپنے کورسز کے بارے میں پوچھیں...',
    submit: 'جمع کریں',
    voice: 'آواز',
    lectures: 'لیکچرز',
    settings: 'ترتیبات',
    lmsCredentials: 'LMS اسناد',
    email: 'ای میل',
    password: 'پاس ورڈ',
    save: 'محفوظ کریں',
    syncNow: 'ابھی ہم آہنگ کریں',
    lastSync: 'آخری ہم آہنگی',
    offline: 'آپ آف لائن ہیں',
  },
} as const;

export type TranslationKey = keyof typeof translations.en;

let currentLanguage: Language = 'en';

export function t(key: TranslationKey): string {
  return translations[currentLanguage][key] ?? key;
}

export function getCurrentLanguage(): Language {
  return currentLanguage;
}

export async function setLanguage(lang: Language): Promise<void> {
  currentLanguage = lang;
  await AsyncStorage.setItem(LANGUAGE_KEY, lang);

  const isRTL = lang === 'ur';
  if (I18nManager.isRTL !== isRTL) {
    I18nManager.forceRTL(isRTL);
    // App restart required for RTL to take full effect
  }
}

export async function loadSavedLanguage(): Promise<void> {
  try {
    const saved = await AsyncStorage.getItem(LANGUAGE_KEY);
    if (saved === 'en' || saved === 'ur') {
      await setLanguage(saved);
    }
  } catch {
    // Use default language
  }
}
