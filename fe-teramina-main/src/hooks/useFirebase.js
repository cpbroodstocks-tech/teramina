import { getAuth, onAuthStateChanged } from "firebase/auth";
import { axios } from "helper/axios";
import { useLocalStorage } from "hooks/useLocalStorage";
import { useFCM } from "hooks/useFCM";
import { initializeTeraminaFirebase } from "libraries/firebase";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "store/user.store";

const useFirebase = () => {
  const { set, get, removeItem } = useLocalStorage()
  const { setUser } = useUserStore()
  useFCM()

  const navigate = useNavigate()
  useEffect(() => {
    let unsubscribe = null

    const initFirebase = async () => {
      try {
        const firebase = await initializeTeraminaFirebase()
        if (!firebase) throw firebase

        const auth = getAuth()
        unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
          if (!currentUser) {
            setUser({})
            return removeItem("authentication")
          }

          if (!get("authentication") && currentUser) {
            const {stsTokenManager} = currentUser
            const validate = await axios.post(`/user/firebase-verify-user?token=${stsTokenManager.accessToken}`);

            if (!validate) throw validate

            set("authentication", validate.payload.token)
            set("refresh_token", validate.payload.refresh_token)

            const user = await axios.get("/user/get-profile")
            if (!user) throw user

            setUser(user.payload)
            return navigate("/dashboard")
          }

          if (get("authentication") && currentUser) {
            const user = await axios.get("/user/get-profile")
            if (!user) throw user

            return setUser(user.payload)
          }
        })

      } catch (err) {
        return navigate("/")
      }
    }

    if (typeof window !== "undefined") initFirebase();

    return () => {
      if (unsubscribe) unsubscribe()
    }
  }, [])
}

export { useFirebase }