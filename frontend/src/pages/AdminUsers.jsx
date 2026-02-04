import React, { useEffect, useState } from 'react';
import { adminService } from '../services/api';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Switch, Select, MenuItem, Button, TextField, Alert, FormControlLabel, Checkbox } from '@mui/material';

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState({ username: '', email: '', password: '', role: 'planning' });
  const [purgeDate, setPurgeDate] = useState('');
  const [includeErp, setIncludeErp] = useState(false);
  const [purgeResult, setPurgeResult] = useState(null);
  const [passwords, setPasswords] = useState({});

  const load = async () => {
    try {
      const data = await adminService.listUsers();
      setUsers(data);
    } catch (e) {
      setError(e.response?.data?.error || 'Error cargando usuarios');
    }
  };

  useEffect(() => { load(); }, []);

  const updateUser = async (id, payload) => {
    try {
      await adminService.updateUser(id, payload);
      await load();
    } catch (e) {
      setError(e.response?.data?.error || 'Error actualizando usuario');
    }
  };

  const createUser = async () => {
    setError('');
    try {
      await adminService.createUser(creating);
      setCreating({ username: '', email: '', password: '', role: 'planning' });
      await load();
    } catch (e) {
      setError(e.response?.data?.error || 'Error creando usuario');
    }
  };


  const updatePassword = async (id) => {
    const newPassword = passwords[id];
    if (!newPassword) {
      setError('Captura una contrasena nueva');
      return;
    }
    try {
      await adminService.updateUser(id, { password: newPassword });
      setPasswords((prev) => ({ ...prev, [id]: '' }));
      await load();
    } catch (e) {
      setError(e.response?.data?.error || 'Error actualizando contrasena');
    }
  };

  const runPurge = async (dryRun) => {
    setError('');
    setPurgeResult(null);
    if (!purgeDate) {
      setError('Selecciona una fecha para depurar');
      return;
    }
    try {
      const result = await adminService.purgeOrders({
        before_date: purgeDate,
        include_erp: includeErp,
        dry_run: dryRun
      });
      setPurgeResult(result);
    } catch (e) {
      setError(e.response?.data?.error || 'Error depurando registros');
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Usuarios</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>Crear usuario</Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField label="Usuario" value={creating.username} onChange={e => setCreating({ ...creating, username: e.target.value })} />
          <TextField label="Email" value={creating.email} onChange={e => setCreating({ ...creating, email: e.target.value })} />
          <TextField label="Contrasena" type="password" value={creating.password} onChange={e => setCreating({ ...creating, password: e.target.value })} />
          <Select value={creating.role} onChange={e => setCreating({ ...creating, role: e.target.value })}>
            <MenuItem value="admin">admin</MenuItem>
            <MenuItem value="planning">planning</MenuItem>
            <MenuItem value="warehouse">warehouse</MenuItem>
            <MenuItem value="purchasing">purchasing</MenuItem>
            <MenuItem value="production">production</MenuItem>
            <MenuItem value="logistics">logistics</MenuItem>
          </Select>
          <Button variant="contained" onClick={createUser}>Crear</Button>
        </Box>
      </Paper>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>Depurar registros por fecha (ordenes locales)</Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            label="Eliminar anteriores a"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={purgeDate}
            onChange={(e) => setPurgeDate(e.target.value)}
          />
          <FormControlLabel
            control={<Checkbox checked={includeErp} onChange={(e) => setIncludeErp(e.target.checked)} />}
            label="Incluir ordenes de ERP (no recomendado)"
          />
          <Button variant="outlined" onClick={() => runPurge(true)}>Previsualizar</Button>
          <Button variant="contained" color="error" onClick={() => runPurge(false)}>Depurar</Button>
        </Box>
        {purgeResult && (
          <Alert severity="info" sx={{ mt: 2 }}>
            {purgeResult.message || 'Resultado de depuracion'}
            {purgeResult.orders_to_delete != null && (
              <span> | Ordenes: {purgeResult.orders_to_delete} | Items: {purgeResult.items_to_delete} | Logs: {purgeResult.production_logs_to_delete}</span>
            )}
            {purgeResult.orders_deleted != null && (
              <span> | Ordenes: {purgeResult.orders_deleted} | Items: {purgeResult.items_deleted} | Logs: {purgeResult.production_logs_deleted}</span>
            )}
          </Alert>
        )}
      </Paper>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Usuario</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Activo</TableCell>
              <TableCell>Contrasena</TableCell>
              <TableCell>Ultimo acceso</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map(u => (
              <TableRow key={u.id}>
                <TableCell>{u.username}</TableCell>
                <TableCell>{u.email}</TableCell>
                <TableCell>
                  <Select value={u.role} onChange={e => updateUser(u.id, { role: e.target.value })} size="small">
                    <MenuItem value="admin">admin</MenuItem>
                    <MenuItem value="planning">planning</MenuItem>
                    <MenuItem value="warehouse">warehouse</MenuItem>
                    <MenuItem value="purchasing">purchasing</MenuItem>
                    <MenuItem value="production">production</MenuItem>
                    <MenuItem value="logistics">logistics</MenuItem>
                  </Select>
                </TableCell>
                <TableCell>
                  <Switch checked={u.is_active} onChange={e => updateUser(u.id, { is_active: e.target.checked })} />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      type="password"
                      placeholder="Nueva"
                      value={passwords[u.id] || ''}
                      onChange={e => setPasswords((prev) => ({ ...prev, [u.id]: e.target.value }))}
                    />
                    <Button size="small" variant="outlined" onClick={() => updatePassword(u.id)}>
                      Cambiar
                    </Button>
                  </Box>
                </TableCell>
                <TableCell>{u.last_login || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
