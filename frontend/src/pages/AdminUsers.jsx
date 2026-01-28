import React, { useEffect, useState } from 'react';
import { adminService } from '../services/api';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, Switch, Select, MenuItem, Button, TextField, Alert } from '@mui/material';

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState({ username: '', email: '', password: '', role: 'user' });

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
      setCreating({ username: '', email: '', password: '', role: 'user' });
      await load();
    } catch (e) {
      setError(e.response?.data?.error || 'Error creando usuario');
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
          <TextField label="Contraseña" type="password" value={creating.password} onChange={e => setCreating({ ...creating, password: e.target.value })} />
          <Select value={creating.role} onChange={e => setCreating({ ...creating, role: e.target.value })}>
            <MenuItem value="admin">admin</MenuItem>
            <MenuItem value="manager">manager</MenuItem>
            <MenuItem value="user">user</MenuItem>
            <MenuItem value="operator">operator</MenuItem>
          </Select>
          <Button variant="contained" onClick={createUser}>Crear</Button>
        </Box>
      </Paper>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Usuario</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Activo</TableCell>
              <TableCell>Último acceso</TableCell>
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
                    <MenuItem value="manager">manager</MenuItem>
                    <MenuItem value="user">user</MenuItem>
                    <MenuItem value="operator">operator</MenuItem>
                  </Select>
                </TableCell>
                <TableCell>
                  <Switch checked={u.is_active} onChange={e => updateUser(u.id, { is_active: e.target.checked })} />
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
