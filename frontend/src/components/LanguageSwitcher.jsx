/**
 * 多语言切换组件
 *
 * 提供界面语言切换功能
 */

import React, { useState, useEffect } from 'react';
import { Globe } from 'lucide-react';
import api from '../api/client';

const LanguageSwitcher = () => {
  const [currentLanguage, setCurrentLanguage] = useState('zh-CN');
  const [translations, setTranslations] = useState({});

  const languages = [
    { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
    { code: 'en-US', name: 'English', flag: '🇺🇸' },
    { code: 'ja-JP', name: '日本語', flag: '🇯🇵' },
    { code: 'ko-KR', name: '한국어', flag: '🇰🇷' },
    { code: 'fr-FR', name: 'Français', flag: '🇫🇷' },
    { code: 'de-DE', name: 'Deutsch', flag: '🇩🇪' },
    { code: 'es-ES', name: 'Español', flag: '🇪🇸' },
    { code: 'ru-RU', name: 'Русский', flag: '🇷🇺' },
    { code: 'ar-SA', name: 'العربية', flag: '🇸🇦' },
    { code: 'pt-BR', name: 'Português', flag: '🇧🇷' }
  ];

  useEffect(() => {
    // 从localStorage加载语言设置
    const saved = localStorage.getItem('language');
    if (saved) {
      setCurrentLanguage(saved);
      loadTranslations(saved);
    }
  }, []);

  const loadTranslations = async (lang) => {
    try {
      const response = await api.get(`/api/i18n/translations/${lang}`);
      setTranslations(response.data.translations);
    } catch (error) {
      console.error('Failed to load translations:', error);
    }
  };

  const handleLanguageChange = async (langCode) => {
    setCurrentLanguage(langCode);
    localStorage.setItem('language', langCode);
    await loadTranslations(langCode);

    // 刷新页面以应用新语言
    window.location.reload();
  };

  const t = (key) => {
    return translations[key] || key;
  };

  return (
    <div className="relative group">
      <button className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100">
        <Globe className="w-5 h-5" />
        <span className="text-sm">
          {languages.find(l => l.code === currentLanguage)?.flag}
        </span>
      </button>

      {/* 下拉菜单 */}
      <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        <div className="py-2">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={`w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center space-x-2 ${
                currentLanguage === lang.code ? 'bg-blue-50 text-blue-600' : ''
              }`}
            >
              <span>{lang.flag}</span>
              <span className="text-sm">{lang.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// 导出翻译函数供其他组件使用
export const useTranslation = () => {
  const [translations, setTranslations] = useState({});

  useEffect(() => {
    const lang = localStorage.getItem('language') || 'zh-CN';
    api.get(`/api/i18n/translations/${lang}`)
      .then(response => setTranslations(response.data.translations))
      .catch(error => console.error('Failed to load translations:', error));
  }, []);

  const t = (key) => translations[key] || key;

  return { t };
};

export default LanguageSwitcher;
