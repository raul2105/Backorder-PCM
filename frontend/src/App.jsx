import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
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

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  const ProtectedRoute = ({ children }) => {
    return isAuthenticated ? children : <Navigate to="/login" />;
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated} />} />
        
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
