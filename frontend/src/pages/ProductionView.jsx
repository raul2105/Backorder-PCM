import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Paper,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Chip,
  Tab,
  Tabs,
} from '@mui/material';
import { productionService, backorderService } from '../services/api';

export default function ProductionView() {
  const [searchTerm, setSearchTerm] = useState('');
  const { data, isLoading, refetch } = useQuery('production', productionService.getLogs);
  const { data: backOrderData } = useQuery(
      ['backorders-prod', searchTerm], 
      () => backorderService.getAll({ search: searchTerm })
  );
  const [error, setError] = useState('');
  const [openForm, setOpenForm] = useState(false);
  const [tabIndex, setTabIndex] = useState(0);
  const [newLog, setNewLog] = useState({
    order_id: '',
    quantity_produced: '',
    operator: '',
    notes: '',
  });

  const handleCreateLog = async () => {
    setError('');
    if (!newLog.order_id || !newLog.quantity_produced) {
      setError('Orden y cantidad requeridos');
      return;
    }
    try {
      await productionService.createLog(newLog);
      setNewLog({ order_id: '', quantity_produced: '', operator: '', notes: '' });
      setOpenForm(false);
      refetch();
    } catch (e) {
      setError(e.response?.data?.error || 'Error registrando producción');
    }
  };

  if (isLoading) {
    return <CircularProgress />;
  }

  const orders = backOrderData?.backorders || [];
  const inProgressOrders = orders.filter(o => o.status === 'in_production');

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Tabs value={tabIndex} onChange={(_, i) => setTabIndex(i)} sx={{ mb: 2 }}>
        <Tab label="Registro de Producción" />
        <Tab label="En Proceso" />
      </Tabs>

      <Box sx={{ mb: 3 }}>
         <TextField
          fullWidth
          size="small"
          label="Buscar Orden"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          variant="outlined"
          placeholder="Ingrese número de orden..."
        />
      </Box>

      {tabIndex === 0 && (
        <Box>
          <Button variant="contained" onClick={() => setOpenForm(true)} sx={{ mb: 2 }}>
            Registrar Producción
          </Button>

          <Paper>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Orden</strong></TableCell>
                  <TableCell><strong>Cantidad</strong></TableCell>
                  <TableCell><strong>Operario</strong></TableCell>
                  <TableCell><strong>Fecha</strong></TableCell>
                  <TableCell><strong>Notas</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(data?.logs || []).map(log => (
                  <TableRow key={log.id}>
                    <TableCell>{log.order_id}</TableCell>
                    <TableCell>{log.quantity_produced}</TableCell>
                    <TableCell>{log.operator}</TableCell>
                    <TableCell>{new Date(log.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>{log.notes}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Box>
      )}

      {tabIndex === 1 && (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Pedido</strong></TableCell>
                <TableCell><strong>Cliente</strong></TableCell>
                <TableCell><strong>Estado</strong></TableCell>
                <TableCell><strong>Prioridad</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {inProgressOrders.map(order => (
                <TableRow key={order.id}>
                  <TableCell>{order.order_number}</TableCell>
                  <TableCell>{order.customer_name}</TableCell>
                  <TableCell><Chip label="En Producción" color="info" /></TableCell>
                  <TableCell>
                    {order.priority === 1 && <Chip label="Urgente" color="error" size="small" />}
                    {order.priority === 2 && <Chip label="Alta" color="warning" size="small" />}
                    {order.priority === 3 && <Chip label="Normal" size="small" />}
                    {order.priority === 4 && <Chip label="Baja" size="small" />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Dialog open={openForm} onClose={() => setOpenForm(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Registrar Producción</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Select
              value={newLog.order_id}
              onChange={e => setNewLog({ ...newLog, order_id: e.target.value })}
              fullWidth
            >
              <MenuItem value="">Seleccionar orden</MenuItem>
              {inProgressOrders.map(o => (
                <MenuItem key={o.id} value={o.id}>
                  {o.order_number} - {o.customer_name}
                </MenuItem>
              ))}
            </Select>
            <TextField
              label="Cantidad Producida"
              type="number"
              value={newLog.quantity_produced}
              onChange={e => setNewLog({ ...newLog, quantity_produced: e.target.value })}
              fullWidth
            />
            <TextField
              label="Operario"
              value={newLog.operator}
              onChange={e => setNewLog({ ...newLog, operator: e.target.value })}
              fullWidth
            />
            <TextField
              label="Notas"
              multiline
              rows={3}
              value={newLog.notes}
              onChange={e => setNewLog({ ...newLog, notes: e.target.value })}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenForm(false)}>Cancelar</Button>
          <Button onClick={handleCreateLog} variant="contained">Guardar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
