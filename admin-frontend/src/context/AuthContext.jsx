import { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const currentUser = await authAPI.getCurrentUser();
        setUser({
          id: currentUser.id,
          email: currentUser.email,
          role: currentUser.role || 'user'
        });
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadCurrentUser();
  }, []);

  const login = async (email, password) => {
    const data = await authAPI.login(email, password);
    const userData = data.user || (await authAPI.getCurrentUser());
    setUser({
      id: userData.id,
      email: userData.email,
      role: userData.role || 'user'
    });
    return userData;
  };

  const logout = () => {
    authAPI.logout?.();
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
