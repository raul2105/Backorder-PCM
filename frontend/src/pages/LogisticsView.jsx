import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert
} from '@mui/material';
import { logisticsService } from '../services/api';
import { format } from 'date-fns';
import StatusChips from '../components/StatusChips';

export default function LogisticsView() {
  const queryClient = useQueryClient();
  const [openShipDialog, setOpenShipDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [trackingInfo, setTrackingInfo] = useState({ carrier: '', trackingNumber: '' });
  const [actionError, setActionError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const { data: pending, isLoading: loadingPending } = useQuery(
    ['pending-shipments', searchTerm],
    () => logisticsService.getPendingShipments({ search: searchTerm }),
    { refetchInterval: 30000 }
  );

  const { data: shipped, isLoading: loadingShipped } = useQuery(
    ['shipped-orders', searchTerm],
    () => logisticsService.getShippedOrders({ search: searchTerm })
  );
  
  const shipMutation = useMutation(
      ({ id, tracking, carrier }) => logisticsService.updateShipment(id, tracking, carrier),
      {
          onSuccess: () => {
              queryClient.invalidateQueries('pending-shipments');
              queryClient.invalidateQueries('shipped-orders');
              handleCloseDialog();
          },
          onError: (error) => {
              setActionError(error.response?.data?.message || 'Error al procesar envío');
          }
      }
  );

  const handleOpenShip = (order) => {
      setSelectedOrder(order);
      setTrackingInfo({ carrier: '', trackingNumber: '' });
      setActionError('');
      setOpenShipDialog(true);
  };

  const handleCloseDialog = () => {
      setOpenShipDialog(false);
      setSelectedOrder(null);
  };

  const handleConfirmShip = () => {
      if (selectedOrder) {
          shipMutation.mutate({
              id: selectedOrder.id,
              tracking: trackingInfo.trackingNumber,
              carrier: trackingInfo.carrier
          });
      }
  };

  if (loadingPending || loadingShipped) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Gestión de Logística
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          size="small"
          label="Buscar por Orden o Cliente"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          variant="outlined"
          placeholder="Ingrese # de orden o nombre de cliente..."
        />
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Órdenes Pendientes de Envío ({pending?.total || 0})
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Orden</TableCell>
                    <TableCell>Cliente</TableCell>
                    <TableCell>Fecha Prometida</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Flujo</TableCell>
                    <TableCell>Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pending?.shipments?.map((order) => (
                    <TableRow key={order.id} hover>
                      <TableCell>{order.order_number}</TableCell>
                      <TableCell>{order.customer_name}</TableCell>
                      <TableCell>
                        {order.promised_date 
                          ? format(new Date(order.promised_date), 'dd/MM/yyyy')
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <Chip label="Listo para Envío" color="success" size="small" />
                      </TableCell>
                      <TableCell>
                        <StatusChips order={order} compact />
                      </TableCell>
                      <TableCell>
                          <Button 
                            variant="contained" 
                            size="small" 
                            color="primary"
                            onClick={() => handleOpenShip(order)}
                          >
                              Registrar Envío
                          </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {pending?.shipments?.length === 0 && (
              <Box textAlign="center" py={2}>
                <Typography color="textSecondary">
                  No hay órdenes pendientes de envío
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Órdenes Enviadas Recientemente ({shipped?.total || 0})
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Orden</TableCell>
                    <TableCell>Cliente</TableCell>
                    <TableCell>Fecha Envío</TableCell>
                    <TableCell>Estado</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {shipped?.shipments?.map((order) => (
                    <TableRow key={order.id} hover>
                      <TableCell>{order.order_number}</TableCell>
                      <TableCell>{order.customer_name}</TableCell>
                      <TableCell>
                        {order.updated_at 
                          ? format(new Date(order.updated_at), 'dd/MM/yyyy HH:mm')
                          : '-'}
                      </TableCell>
                      <TableCell>
                        <Chip label="Enviado" color="info" size="small" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {shipped?.shipments?.length === 0 && (
              <Box textAlign="center" py={2}>
                <Typography color="textSecondary">
                  No hay órdenes enviadas recientemente
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {/* Ship Dialog */}
      <Dialog open={openShipDialog} onClose={handleCloseDialog}>
          <DialogTitle>Registrar Envío: {selectedOrder?.order_number}</DialogTitle>
          <DialogContent>
              <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 300 }}>
                  {actionError && <Alert severity="error">{actionError}</Alert>}
                  <TextField 
                      label="Paquetería / Chofer"
                      fullWidth
                      value={trackingInfo.carrier}
                      onChange={(e) => setTrackingInfo({...trackingInfo, carrier: e.target.value})}
                  />
                  <TextField 
                      label="Número de Rastreo / Placas"
                      fullWidth
                      value={trackingInfo.trackingNumber}
                      onChange={(e) => setTrackingInfo({...trackingInfo, trackingNumber: e.target.value})}
                  />
                  <Typography variant="caption" color="textSecondary">
                      * Esta acción marcará la orden como enviada y saldrá de la lista de pendientes.
                  </Typography>
              </Box>
          </DialogContent>
          <DialogActions>
              <Button onClick={handleCloseDialog}>Cancelar</Button>
              <Button onClick={handleConfirmShip} variant="contained" color="primary" disabled={shipMutation.isLoading}>
                  {shipMutation.isLoading ? 'Procesando...' : 'Confirmar Envío'}
              </Button>
          </DialogActions>
      </Dialog>
    </Box>
  );
}
