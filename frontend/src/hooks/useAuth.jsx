import { createContext, useContext, useState, useEffect } from "react";
import { registerCitizen, loginCitizen } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("userId");
    if (token && userId) setUser({ token, userId });
    setLoading(false);
  }, []);

  const register = async (formData) => {
    const res = await registerCitizen(formData);
    localStorage.setItem("token", res.data.access_token);
    localStorage.setItem("userId", res.data.user_id);
    setUser({ token: res.data.access_token, userId: res.data.user_id });
    return res.data;
  };

  const login = async (formData) => {
    const res = await loginCitizen(formData);
    localStorage.setItem("token", res.data.access_token);
    localStorage.setItem("userId", res.data.user_id);
    setUser({ token: res.data.access_token, userId: res.data.user_id });
    return res.data;
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
