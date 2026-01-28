import React, { useEffect, useState } from 'react';
import { settingsService } from '../services/api';
import { Box, Typography, Paper, TextField, Button, Alert } from '@mui/material';

export default function NetworkSettings() {
  const [allowed, setAllowed] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const load = async () => {
    setError('');
    try {
      const { allowed_ips } = await settingsService.getNetwork();
      setAllowed((allowed_ips || []).join(', '));
    } catch (e) {
      setError(e.response?.data?.error || 'Error cargando configuración');
    }
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    setError(''); setMessage('');
    try {
      const arr = allowed.split(',').map(s => s.trim()).filter(Boolean);
      await settingsService.updateNetwork(arr);
      setMessage('Configuración guardada');
    } catch (e) {
      setError(e.response?.data?.error || 'Error guardando configuración');
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Configuración de Red</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}
      <Paper sx={{ p: 2 }}>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Lista de IPs/CIDR permitidos (separados por coma). Ejemplo: 192.168.0.0/24, 10.0.0.5
        </Typography>
        <TextField fullWidth multiline minRows={3} value={allowed} onChange={e => setAllowed(e.target.value)} />
        <Button variant="contained" sx={{ mt: 2 }} onClick={save}>Guardar</Button>
      </Paper>
    </Box>
  );
}
