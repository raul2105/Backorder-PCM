import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
} from '@mui/material';
import { authService } from '../services/api';

export default function Login({ setIsAuthenticated, setMustChangePassword }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await authService.login(username, password);

      // Actualizar estado en App
      setIsAuthenticated(true);

      // Verificar si el usuario debe cambiar contrasena
      let mustChange = result?.user?.must_change_password === true;
      if (result?.access_token) {
        localStorage.setItem('token', result.access_token);
      }
      if (result?.user) {
        localStorage.setItem('user', JSON.stringify(result.user));
      }
      if (result?.user?.must_change_password == null) {
        try {
          const currentUser = await authService.getCurrentUser();
          mustChange = currentUser?.must_change_password === true;
        } catch {
          // Si falla, mantener valor actual
        }
      }
      setMustChangePassword(mustChange);

      // Redirigir segun el resultado
      if (mustChange) {
        navigate('/change-password');
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" gutterBottom>
            Backorder PCM
          </Typography>
          <Typography variant="body2" align="center" color="textSecondary" sx={{ mb: 3 }}>
            Sistema de Gestión de Backorder
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} noValidate>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Usuario"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Contraseña"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </Box>

          <Typography variant="caption" color="textSecondary" align="center" display="block">
            Usuario por defecto: admin / admin123
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
}
