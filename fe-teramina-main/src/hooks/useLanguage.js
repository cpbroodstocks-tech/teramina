import i18next from "i18next";

const useLanguage = () => {
  return {
    setLang: (lang) => {
      i18next.changeLanguage(lang);
      localStorage.setItem("lang", lang);
    },
    getLang: () => {
      const lang = localStorage.getItem("lang");
      return lang;
    },
  };
};

export { useLanguage };
