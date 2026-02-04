import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Páginas
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import BackorderList from './pages/BackorderList';
import CreateOrder from './pages/CreateOrder';
import MaterialInventory from './pages/MaterialInventory';
import ProductionView from './pages/ProductionView';
import LogisticsView from './pages/LogisticsView';
import AdminUsers from './pages/AdminUsers';
import NetworkSettings from './pages/NetworkSettings';
import ChangePassword from './pages/ChangePassword';
import { authService } from './services/api';

// Componentes
import Layout from './components/Layout';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const location = useLocation();
  // Actualizar estado de autenticación desde localStorage
  const updateAuthState = () => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    setIsAuthenticated(!!token);
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setMustChangePassword(!!user?.must_change_password);
      } catch {
        setMustChangePassword(false);
      }
    } else {
      setMustChangePassword(false);
    }
  };

  useEffect(() => {
    updateAuthState();
    const token = localStorage.getItem('token');
    if (token) {
      authService.getCurrentUser().then(updateAuthState).catch(() => {});
    }
    // Escuchar cambios en localStorage (cuando se actualiza desde otra pestaña o el mismo contexto)
    const handleStorageChange = () => {
      updateAuthState();
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const ProtectedRoute = ({ children }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" />;
    }
    if (mustChangePassword && location.pathname !== '/change-password') {
      return <Navigate to="/change-password" />;
    }
    return isAuthenticated ? children : <Navigate to="/login" />;
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route
          path="/login"
          element={
            <Login
              setIsAuthenticated={setIsAuthenticated}
              setMustChangePassword={setMustChangePassword}
            />
          }
        />
        <Route
          path="/change-password"
          element={
            <ProtectedRoute>
              <ChangePassword onPasswordChanged={() => setMustChangePassword(false)} />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="backorder" element={<BackorderList />} />
          <Route path="backorder/new" element={<CreateOrder />} />
          <Route path="materials" element={<MaterialInventory />} />
          <Route path="production" element={<ProductionView />} />
          <Route path="logistics" element={<LogisticsView />} />
          <Route path="admin/users" element={<AdminUsers />} />
          <Route path="admin/network" element={<NetworkSettings />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App;
