import i18next from "i18next";
import { initReactI18next } from "react-i18next";

import EN from "locales/resources/en.json";
import ID from "locales/resources/id.json";

const language = localStorage.getItem("lang") ?? "en";
localStorage.setItem("lang", language);

const resources = {
  en: {
    translation: EN,
  },
  id: {
    translation: ID,
  },
};

i18next.use(initReactI18next).init({
  lng: language,
  fallbackLng: language,
  ns: ["translation"],
  defaultNS: "translation",
  resources: resources,
  keySeparator: false,
  detection: {
    caches: ["localStorage"],
  },
});

export default i18next;
