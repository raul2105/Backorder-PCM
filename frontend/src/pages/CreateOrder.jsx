import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from 'react-query';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  IconButton,
  Divider,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { backorderService } from '../services/api';

export default function CreateOrder() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  
  // General Info
  const [formData, setFormData] = useState({
    order_number: '',
    customer_code: '',
    customer_name: '',
    sales_rep: '',
    priority: 3,
    promised_date: '',
    backorder_reason: ''
  });

  // Items
  const [items, setItems] = useState([
    { item_code: '', quantity: '', unit: 'PZA', description: '', work_order: '' }
  ]);

  const createMutation = useMutation(
    (data) => backorderService.create(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('backorders');
        navigate('/backorder');
      },
      onError: (err) => {
        setError(err.response?.data?.error || 'Error creando orden');
      }
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.order_number || !formData.customer_code) {
      setError('Número de orden y código de cliente son requeridos');
      return;
    }
    
    // Validate items
    const validItems = items.filter(i => i.item_code && i.quantity);
    if (validItems.length === 0) {
      setError('Debe agregar al menos un ítem válido (código y cantidad)');
      return;
    }

    createMutation.mutate({
      ...formData,
      items: validItems
    });
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  const handleAddItem = () => {
    setItems([...items, { item_code: '', quantity: '', unit: 'PZA', description: '', work_order: '' }]);
  };

  const handleRemoveItem = (index) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/backorder')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">
          Nueva Orden Manual
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <form onSubmit={handleSubmit}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Datos Generales</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Número de Orden / Pedido"
                value={formData.order_number}
                onChange={(e) => handleChange('order_number', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Código Cliente"
                value={formData.customer_code}
                onChange={(e) => handleChange('customer_code', e.target.value)}
                required
                helperText="Si no existe, se creará"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Nombre Cliente (Opcional)"
                value={formData.customer_name}
                onChange={(e) => handleChange('customer_name', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="date"
                label="Fecha Promesa"
                InputLabelProps={{ shrink: true }}
                value={formData.promised_date}
                onChange={(e) => handleChange('promised_date', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Prioridad</InputLabel>
                <Select
                  value={formData.priority}
                  label="Prioridad"
                  onChange={(e) => handleChange('priority', e.target.value)}
                >
                  <MenuItem value={1}>Urgente</MenuItem>
                  <MenuItem value={2}>Alta</MenuItem>
                  <MenuItem value={3}>Normal</MenuItem>
                  <MenuItem value={4}>Baja</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Vendedor"
                value={formData.sales_rep}
                onChange={(e) => handleChange('sales_rep', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Razón de Backorder"
                value={formData.backorder_reason}
                onChange={(e) => handleChange('backorder_reason', e.target.value)}
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Items</Typography>
            <Button startIcon={<AddIcon />} onClick={handleAddItem} variant="outlined" size="small">
              Agregar Item
            </Button>
          </Box>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell width="20%">Código / SKU</TableCell>
                <TableCell width="25%">Descripción</TableCell>
                <TableCell width="15%">Cantidad</TableCell>
                <TableCell width="15%">Unidad</TableCell>
                <TableCell width="15%">Orden Trabajo (OT)</TableCell>
                <TableCell width="10%"></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="SKU-123"
                      value={item.item_code}
                      onChange={(e) => handleItemChange(index, 'item_code', e.target.value)}
                    />
                  </TableCell>
                  <TableCell>
                     <TextField
                      fullWidth
                      size="small"
                      value={item.description}
                      onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                    />
                  </TableCell>
                  <TableCell>
                     <TextField
                      fullWidth
                      type="number"
                      size="small"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                    />
                  </TableCell>
                  <TableCell>
                    <Select
                      fullWidth
                      size="small"
                      value={item.unit}
                      onChange={(e) => handleItemChange(index, 'unit', e.target.value)}
                    >
                      <MenuItem value="PZA">PZA</MenuItem>
                      <MenuItem value="ROLLO">ROLLO</MenuItem>
                      <MenuItem value="CJ">CAJA</MenuItem>
                      <MenuItem value="MILLAR">MILLAR</MenuItem>
                    </Select>
                  </TableCell>
                  <TableCell>
                     <TextField
                      fullWidth
                      size="small"
                      value={item.work_order}
                      onChange={(e) => handleItemChange(index, 'work_order', e.target.value)}
                    />
                  </TableCell>
                  <TableCell>
                    {items.length > 1 && (
                      <IconButton color="error" onClick={() => handleRemoveItem(index)}>
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>

        <Box display="flex" justifyContent="flex-end" gap={2}>
           <Button variant="outlined" onClick={() => navigate('/backorder')}>
             Cancelar
           </Button>
           <Button type="submit" variant="contained" color="primary" disabled={createMutation.isLoading}>
             {createMutation.isLoading ? 'Guardando...' : 'Crear Orden'}
           </Button>
        </Box>
      </form>
    </Box>
  );
}
