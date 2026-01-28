import React from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { materialService } from '../services/api';

export default function MaterialInventory() {
  const { data: materials, isLoading } = useQuery(
    'materials',
    () => materialService.getAll(),
    { refetchInterval: 30000 }
  );

  const { data: alerts } = useQuery(
    'material-alerts',
    materialService.getAlerts
  );

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
        Inventario de Materiales
      </Typography>

      {alerts && alerts.total_alerts > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Hay {alerts.total_alerts} materiales con stock bajo que requieren atención
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Código</TableCell>
              <TableCell>Descripción</TableCell>
              <TableCell>Categoría</TableCell>
              <TableCell align="right">Disponible</TableCell>
              <TableCell align="right">Reservado</TableCell>
              <TableCell align="right">En Pedido</TableCell>
              <TableCell align="right">Stock Mínimo</TableCell>
              <TableCell>Proveedor</TableCell>
              <TableCell>Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {materials?.materials?.map((material) => {
              const isLowStock = material.quantity_available <= material.minimum_stock;
              return (
                <TableRow key={material.id} hover sx={{ 
                  backgroundColor: isLowStock ? '#fff3e0' : 'inherit' 
                }}>
                  <TableCell>{material.material_code}</TableCell>
                  <TableCell>{material.description}</TableCell>
                  <TableCell>{material.category || '-'}</TableCell>
                  <TableCell align="right">
                    {material.quantity_available} {material.unit}
                  </TableCell>
                  <TableCell align="right">
                    {material.quantity_reserved} {material.unit}
                  </TableCell>
                  <TableCell align="right">
                    {material.quantity_on_order} {material.unit}
                  </TableCell>
                  <TableCell align="right">
                    {material.minimum_stock} {material.unit}
                  </TableCell>
                  <TableCell>{material.supplier_name || '-'}</TableCell>
                  <TableCell>
                    {isLowStock ? (
                      <Chip label="Stock Bajo" color="warning" size="small" />
                    ) : (
                      <Chip label="Normal" color="success" size="small" variant="outlined" />
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {materials?.materials?.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="textSecondary">
            No hay materiales registrados
          </Typography>
        </Box>
      )}
    </Box>
  );
}
