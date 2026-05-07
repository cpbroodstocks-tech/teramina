import { useLocalStorage } from "hooks/useLocalStorage";
import { Navigate } from "react-router-dom";

const PrivateRoute = ({ children }) => {
  const { get } = useLocalStorage();
  const isAuthenticated = get("authentication");
  if (isAuthenticated) return children;
  return <Navigate to="/signin" />;
};

export default PrivateRoute;
