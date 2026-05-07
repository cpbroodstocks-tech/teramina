const useLocalStorage = () => ({
  get: (key) => {
    try {
      return JSON.parse(localStorage.getItem(key))
    } catch {
      return null
    }
  },
  set: (key, value) => {
    return localStorage.setItem(key, JSON.stringify(value))
  },
  removeItem: (key) => {
    return localStorage.removeItem(key)
  }
})

export { useLocalStorage }
