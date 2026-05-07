import { useCallback, useRef } from "react"

const useDebounce = (callback, delay = 1000) => {
  const timeoutRef = useRef(null)

  return useCallback((...args) => {
    clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      callback(...args)
    }, delay)
  }, [callback, delay])
}

export { useDebounce }
