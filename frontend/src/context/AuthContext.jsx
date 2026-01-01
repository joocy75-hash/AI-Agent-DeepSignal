import { createContext, useState, useContext, useEffect, useCallback, useMemo } from 'react';
import { authAPI } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Token refresh function
  const refreshAccessToken = useCallback(async () => {
    try {
      console.log('[Auth] Attempting to refresh access token...');
      await authAPI.refreshToken();
      console.log('[Auth] Access token refreshed successfully');
      return true;
    } catch (error) {
      console.error('[Auth] Failed to refresh token:', error);
      // If refresh fails, logout the user
      logout();
      return null;
    }
  }, []);

  // Initialize auth state from localStorage
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

  /**
   * 로그인 함수
   * @param {string} email 
   * @param {string} password 
   * @param {string} totpCode - 2FA 코드 (선택적)
   * @returns 로그인 결과 또는 2FA 필요 여부
   */
  const login = async (email, password, totpCode = null) => {
    const data = await authAPI.login(email, password, totpCode);

    // 2FA가 필요한 경우
    if (data.requires_2fa) {
      return {
        requires_2fa: true,
        user_id: data.user_id
      };
    }

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

  // Memoize context value to prevent unnecessary re-renders of consumers
  const value = useMemo(() => ({
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
    refreshAccessToken,
  }), [user, login, logout, loading, refreshAccessToken]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
