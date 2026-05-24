import { getAuth, onAuthStateChanged } from "firebase/auth";
import { useLocalStorage } from "hooks/useLocalStorage";
import { useFCM } from "hooks/useFCM";
import { initializeTeraminaFirebase } from "libraries/firebase";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "store/user.store";
import { fetchUserProfile, verifyFirebaseUser } from "features/user/queries";

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
            const validate = await verifyFirebaseUser(stsTokenManager.accessToken);

            if (!validate) throw validate

            set("authentication", validate.token)
            set("refresh_token", validate.refresh_token)

            const user = await fetchUserProfile()
            if (!user) throw user

            setUser(user)
            return navigate("/dashboard")
          }

          if (get("authentication") && currentUser) {
            const user = await fetchUserProfile()
            if (!user) throw user

            return setUser(user)
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
