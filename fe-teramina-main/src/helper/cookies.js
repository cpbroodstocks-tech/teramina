import Cookies from "universal-cookie";

const COOKIE_EXPIRES = { path: "/", expires: new Date(Date.now() + (60 * 60 * 24 * 1000 * 7)) };

const TERAMINA_COOKIES = {
  cookies: new Cookies(),
  initCookies(orion) {
    this.cookies.set(import.meta.env.REACT_APP_COOKIE_KEY, orion, COOKIE_EXPIRES)
  },
  getCookies(key) {
    const orionCookies = this.cookies.get(import.meta.env.REACT_APP_COOKIE_KEY);
    if (typeof orionCookies === "undefined") return;
    if (key) {
      return orionCookies[key];
    }
    return orionCookies;
  },
  setCookies(key, value) {
    const orionCookies = this.getCookies();
    if (typeof orionCookies === "undefined") return;
    orionCookies[key] = value;
    return this.cookies.set(import.meta.env.REACT_APP_COOKIE_KEY, orionCookies, COOKIE_EXPIRES)
  },
  removeCookies(key) {
    const orionCookies = this.getCookies();
    if (typeof orionCookies === "undefined") return;
    if (orionCookies && key && typeof orionCookies[key] !== "undefined") {
      delete orionCookies[key]
      return this.cookies.set(import.meta.env.REACT_APP_COOKIE_KEY, orionCookies, COOKIE_EXPIRES)
    }
    return this.cookies.remove(import.meta.env.REACT_APP_COOKIE_KEY, { path: "/" })
  },
  updateCookies(key, value) {
    const orionCookies = this.getCookies();
    if (typeof orionCookies === "undefined") return;
    if (orionCookies && typeof orionCookies[key] !== "undefined") {
      orionCookies[key] = value
    }
    return this.cookies.set(import.meta.env.REACT_APP_COOKIE_KEY, orionCookies, COOKIE_EXPIRES)
  },
}

export { TERAMINA_COOKIES as cookie } 