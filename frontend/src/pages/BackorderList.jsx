import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { format } from 'date-fns';
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
  Chip,
  CircularProgress,
  Alert,
  Checkbox,
  TablePagination,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  TableContainer,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { backorderService } from '../services/api';
import StatusChips from '../components/StatusChips';

const STATUS_LABELS = {
  pending: 'Pendiente',
  in_production: 'En Producción',
  ready: 'Listo',
  shipped: 'Enviado',
  delivered: 'Entregado',
};

const PRIORITY_LABELS = {
  1: 'Urgente',
  2: 'Alta',
  3: 'Normal',
  4: 'Baja',
};

export default function BackorderList() {
  const [filters, setFilters] = useState({ status: '', search: '' });
  const [selected, setSelected] = useState([]);
  const [openDetail, setOpenDetail] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [itemData, setItemData] = useState({});
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const { data, isLoading, refetch } = useQuery(
    ['backorders', filters],
    () => backorderService.getAll(filters),
    { refetchInterval: 15000 }
  );

  const { data: detailData, isLoading: detailLoading } = useQuery(
    ['backorder', currentOrder?.id],
    () => backorderService.getById(currentOrder.id),
    { enabled: !!currentOrder && openDetail }
  );

  const activeOrder = detailData?.order || currentOrder;
  const items = detailData?.items || [];
  
  const [updatingDept, setUpdatingDept] = useState(false);

  const handleUpdateDeptStatus = async (dept, status) => {
      setUpdatingDept(true);
      try {
          await backorderService.updateDepartmentStatus(activeOrder.id, dept, status);
          refetch(); // Refetch list
          // Refetch details handled by useQuery built-in mechanic or we can invalidate query
      } catch (e) {
          setError('Error actualizando estado del departamento');
      } finally {
          setUpdatingDept(false);
      }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelected(filtered.map(o => o.id));
    } else {
      setSelected([]);
    }
  };

  const handleSelect = (id) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleOpenDetail = (order) => {
    setCurrentOrder(order);
    setOpenDetail(true);
  };

  const handleCloseDetail = () => {
    setOpenDetail(false);
    setCurrentOrder(null);
    setEditingItem(null);
  };

  const handleStatusChange = async (orderId, newStatus) => {
    setError('');
    try {
      await backorderService.updateStatus(orderId, newStatus);
      refetch();
    } catch (e) {
      setError(e.response?.data?.error || 'Error actualizando estado');
    }
  };

  const handlePriorityChange = async (orderId, newPriority) => {
    setError('');
    try {
      await backorderService.updatePriority(orderId, newPriority);
      refetch();
    } catch (e) {
      setError(e.response?.data?.error || 'Error actualizando prioridad');
    }
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setItemData({
      quantity_produced: item.quantity_produced || 0,
      quantity_shipped: item.quantity_shipped || 0,
    });
  };

  const handleSaveItem = async () => {
    if (!currentOrder) return;
    try {
      await backorderService.updateItem(currentOrder.id, editingItem.id, itemData);
      setEditingItem(null);
      refetch();
    } catch (e) {
      setError(e.response?.data?.error || 'Error actualizando item');
    }
  };

  const handleBatchStatusUpdate = async (newStatus) => {
    if (!newStatus || selected.length === 0) return;
    setError('');
    try {
      await backorderService.batchUpdateStatus(selected, newStatus);
      setSelected([]);
      refetch();
    } catch (e) {
      setError(e.response?.data?.error || 'Error actualizando estados');
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
    setPage(0);
  };

  const filtered = data?.backorders || [];
  const paginatedOrders = filtered.slice(page * rowsPerPage, (page + 1) * rowsPerPage);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Planeación de Backorders
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              label="Buscar por Orden o Cliente"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Estado</InputLabel>
              <Select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                label="Estado"
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="pending">Pendiente</MenuItem>
                <MenuItem value="in_production">En Producción</MenuItem>
                <MenuItem value="ready">Listo</MenuItem>
                <MenuItem value="shipped">Enviado</MenuItem>
                <MenuItem value="delivered">Entregado</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          {selected.length > 0 && (
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Cambiar estado masivo</InputLabel>
                <Select
                  value=""
                  onChange={(e) => {
                    if (e.target.value) handleBatchStatusUpdate(e.target.value);
                  }}
                  label="Cambiar estado masivo"
                >
                  <MenuItem value="">Seleccionar...</MenuItem>
                  <MenuItem value="pending">Pendiente</MenuItem>
                  <MenuItem value="in_production">En Producción</MenuItem>
                  <MenuItem value="ready">Listo</MenuItem>
                  <MenuItem value="shipped">Enviado</MenuItem>
                  <MenuItem value="delivered">Entregado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
          {selected.length > 0 && (
            <Grid item xs={12}>
              <Chip label={`${selected.length} seleccionados`} color="primary" />
            </Grid>
          )}
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selected.length === paginatedOrders.length && paginatedOrders.length > 0}
                  indeterminate={selected.length > 0 && selected.length < paginatedOrders.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell><strong>Orden / OT</strong></TableCell>
              <TableCell><strong>Cliente</strong></TableCell>
              <TableCell><strong>F. Orden</strong></TableCell>
              <TableCell><strong>F. Prometida</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
              <TableCell><strong>Flujo</strong></TableCell>
              <TableCell><strong>Prioridad</strong></TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedOrders.map(order => (
              <TableRow key={order.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.includes(order.id)}
                    onChange={() => handleSelect(order.id)}
                  />
                </TableCell>
                <TableCell>
                    {order.order_number}
                    {order.work_order && (
                        <Typography variant="caption" display="block" color="textSecondary">
                            OT: {order.work_order}
                        </Typography>
                    )}
                </TableCell>
                <TableCell>{order.customer_name}</TableCell>
                <TableCell>
                  {order.order_date ? format(new Date(order.order_date), 'dd/MM/yyyy') : '-'}
                </TableCell>
                <TableCell>
                  {order.promised_date ? format(new Date(order.promised_date), 'dd/MM/yyyy') : '-'}
                </TableCell>
                <TableCell>
                  <Select
                    value={order.status}
                    onChange={e => handleStatusChange(order.id, e.target.value)}
                    size="small"
                  >
                    <MenuItem value="pending">Pendiente</MenuItem>
                    <MenuItem value="in_production">En Producción</MenuItem>
                    <MenuItem value="ready">Listo</MenuItem>
                    <MenuItem value="shipped">Enviado</MenuItem>
                    <MenuItem value="delivered">Entregado</MenuItem>
                  </Select>
                </TableCell>
                <TableCell>
                  <StatusChips order={order} compact />
                </TableCell>
                <TableCell>
                  <Select
                    value={order.priority || 3}
                    onChange={e => handlePriorityChange(order.id, e.target.value)}
                    size="small"
                  >
                    <MenuItem value={1}>Urgente</MenuItem>
                    <MenuItem value={2}>Alta</MenuItem>
                    <MenuItem value={3}>Normal</MenuItem>
                    <MenuItem value={4}>Baja</MenuItem>
                  </Select>
                </TableCell>
                <TableCell>
                  <Button size="small" variant="outlined" onClick={() => handleOpenDetail(order)}>
                    Detalles / Planear
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filtered.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          onRowsPerPageChange={e => setRowsPerPage(parseInt(e.target.value, 10))}
        />
      </TableContainer>

      <Dialog open={openDetail} onClose={handleCloseDetail} maxWidth="lg" fullWidth>
        <DialogTitle>
          Detalles: {activeOrder?.order_number} - {activeOrder?.customer_name}
        </DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {detailLoading ? (
             <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
             </Box>
          ) : (
            <>
              {activeOrder && (
                <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <StatusChips order={activeOrder} />
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    <Grid item xs={12} md={4}>
                        <Typography variant="body2">
                            <strong>Vendedor:</strong> {activeOrder.sales_rep || 'N/A'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Typography variant="body2">
                            <strong>Total:</strong> ${activeOrder.total_amount?.toLocaleString()}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} md={4}>
                         <Typography variant="body2">
                             <strong>Promesa:</strong> {activeOrder.promised_date ? format(new Date(activeOrder.promised_date), 'dd/MM/yyyy') : '-'}
                         </Typography>
                    </Grid>
                  </Grid>
                  {activeOrder.customer_service_notes && (
                     <Typography variant="body2" sx={{ mt: 1, p: 1, bgcolor: '#f5f5f5', borderRadius: 1, whiteSpace: 'pre-wrap' }}>
                        <strong>Notas:</strong> {activeOrder.customer_service_notes}
                     </Typography>
                  )}
                  
                  <Box sx={{ mt: 2 }}>
                     <Accordion disableGutters elevation={0} sx={{ border: '1px solid #e0e0e0', borderRadius: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                           <Typography variant="subtitle2">Gestionar Flujo por Departamento</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                           <Grid container spacing={2}>
                              <Grid item xs={12} sm={4}>
                                 <FormControl fullWidth size="small">
                                    <InputLabel>Planeación</InputLabel>
                                    <Select 
                                        label="Planeación" 
                                        value={activeOrder.planning_status || 'pending'}
                                        onChange={(e) => handleUpdateDeptStatus('planning_status', e.target.value)}
                                        disabled={updatingDept}
                                    >
                                        <MenuItem value="pending">Pendiente</MenuItem>
                                        <MenuItem value="approved">Aprobado</MenuItem>
                                        <MenuItem value="rejected">Rechazado</MenuItem>
                                    </Select>
                                 </FormControl>
                              </Grid>
                              <Grid item xs={12} sm={4}>
                                 <FormControl fullWidth size="small">
                                    <InputLabel>Almacén</InputLabel>
                                    <Select 
                                        label="Almacén" 
                                        value={activeOrder.warehouse_status || 'pending'}
                                        onChange={(e) => handleUpdateDeptStatus('warehouse_status', e.target.value)}
                                        disabled={updatingDept}
                                    >
                                        <MenuItem value="pending">Pendiente</MenuItem>
                                        <MenuItem value="material_available">Dispoible</MenuItem>
                                        <MenuItem value="material_missing">Faltante</MenuItem>
                                    </Select>
                                 </FormControl>
                              </Grid>
                               <Grid item xs={12} sm={4}>
                                 <FormControl fullWidth size="small">
                                    <InputLabel>Compras</InputLabel>
                                    <Select 
                                        label="Compras" 
                                        value={activeOrder.purchasing_status || 'pending'}
                                        onChange={(e) => handleUpdateDeptStatus('purchasing_status', e.target.value)}
                                        disabled={updatingDept}
                                    >
                                        <MenuItem value="pending">Pendiente</MenuItem>
                                        <MenuItem value="ordered">Ordenado</MenuItem>
                                        <MenuItem value="received">Recibido</MenuItem>
                                    </Select>
                                 </FormControl>
                              </Grid>
                               <Grid item xs={12} sm={4}>
                                 <FormControl fullWidth size="small">
                                    <InputLabel>Producción</InputLabel>
                                    <Select 
                                        label="Producción" 
                                        value={activeOrder.production_status || 'pending'}
                                        onChange={(e) => handleUpdateDeptStatus('production_status', e.target.value)}
                                        disabled={updatingDept}
                                    >
                                        <MenuItem value="pending">Pendiente</MenuItem>
                                        <MenuItem value="in_process">En Proceso</MenuItem>
                                        <MenuItem value="completed">Completado</MenuItem>
                                    </Select>
                                 </FormControl>
                              </Grid>
                               <Grid item xs={12} sm={4}>
                                 <FormControl fullWidth size="small">
                                    <InputLabel>Logística</InputLabel>
                                    <Select 
                                        label="Logística" 
                                        value={activeOrder.logistics_status || 'pending'}
                                        onChange={(e) => handleUpdateDeptStatus('logistics_status', e.target.value)}
                                        disabled={updatingDept}
                                    >
                                        <MenuItem value="pending">Pendiente</MenuItem>
                                        <MenuItem value="ready_to_ship">Listo para Envío</MenuItem>
                                        <MenuItem value="shipped">Enviado</MenuItem>
                                    </Select>
                                 </FormControl>
                              </Grid>
                           </Grid>
                        </AccordionDetails>
                     </Accordion>
                  </Box>
                </Box>
              )}
              <Box sx={{ mt: 2 }}>
                <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>OT</strong></TableCell>
                      <TableCell><strong>SKU</strong></TableCell>
                      <TableCell><strong>Descripción</strong></TableCell>
                      <TableCell><strong>Specs</strong></TableCell>
                      <TableCell><strong>Ordenado</strong></TableCell>
                      <TableCell><strong>Producido</strong></TableCell>
                      <TableCell><strong>Enviado</strong></TableCell>
                      <TableCell><strong>Acciones</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map(item => (
                      <TableRow key={item.id}>
                        <TableCell>{item.work_order || '-'}</TableCell>
                        <TableCell>{item.item_code}</TableCell>
                        <TableCell>{item.description || item.item_description}</TableCell>
                        <TableCell>
                            <Box sx={{ fontSize: '0.75rem', maxHeight: 100, overflowY: 'auto' }}>
                            {item.specifications && Object.entries(item.specifications).map(([k, v]) => (
                                <div key={k}><span style={{fontWeight: 500}}>{k}:</span> {v}</div>
                            ))}
                            </Box>
                        </TableCell>
                        <TableCell>{item.quantity_ordered} {item.unit}</TableCell>
                        <TableCell>
                          {editingItem?.id === item.id ? (
                            <TextField
                              type="number"
                              value={itemData.quantity_produced}
                              onChange={e => setItemData({ ...itemData, quantity_produced: parseFloat(e.target.value) || 0 })}
                              size="small"
                              inputProps={{ step: '0.01' }}
                            />
                          ) : (
                            item.quantity_produced
                          )}
                        </TableCell>
                        <TableCell>
                          {editingItem?.id === item.id ? (
                            <TextField
                              type="number"
                              value={itemData.quantity_shipped}
                              onChange={e => setItemData({ ...itemData, quantity_shipped: parseFloat(e.target.value) || 0 })}
                              size="small"
                              inputProps={{ step: '0.01' }}
                            />
                          ) : (
                            item.quantity_shipped
                          )}
                        </TableCell>
                        <TableCell>
                          {editingItem?.id === item.id ? (
                            <>
                              <Button size="small" onClick={handleSaveItem}>Guardar</Button>
                              <Button size="small" onClick={() => setEditingItem(null)}>Cancelar</Button>
                            </>
                          ) : (
                            <Button size="small" onClick={() => handleEditItem(item)}>Editar</Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {items.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={8} align="center">No hay items</TableCell>
                        </TableRow>
                    )}
                  </TableBody>
                </Table>
                </TableContainer>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetail}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
