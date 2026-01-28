import React from 'react';
import { Chip, Stack } from '@mui/material';

const labelMap = {
  planning_status: {
    pending: 'Planeación: Pendiente',
    approved: 'Planeación: Aprobado',
    rejected: 'Planeación: Rechazado'
  },
  warehouse_status: {
    pending: 'Almacén: Pendiente',
    material_available: 'Almacén: Material Disponible',
    material_missing: 'Almacén: Falta Material'
  },
  purchasing_status: {
    pending: 'Compras: Pendiente',
    ordered: 'Compras: Ordenado',
    received: 'Compras: Recibido'
  },
  production_status: {
    pending: 'Producción: Pendiente',
    in_process: 'Producción: En Proceso',
    completed: 'Producción: Completado'
  },
  logistics_status: {
    pending: 'Logística: Pendiente',
    ready_to_ship: 'Logística: Listo para Envío',
    shipped: 'Logística: Enviado'
  }
};

const colorMap = {
  planning_status: {
    pending: 'default',
    approved: 'success',
    rejected: 'error'
  },
  warehouse_status: {
    pending: 'default',
    material_available: 'success',
    material_missing: 'warning'
  },
  purchasing_status: {
    pending: 'default',
    ordered: 'info',
    received: 'success'
  },
  production_status: {
    pending: 'default',
    in_process: 'warning',
    completed: 'success'
  },
  logistics_status: {
    pending: 'default',
    ready_to_ship: 'success',
    shipped: 'info'
  }
};

export default function StatusChips({ order, compact = false }) {
  const statuses = [
    'planning_status',
    'warehouse_status',
    'purchasing_status',
    'production_status',
    'logistics_status'
  ];

  return (
    <Stack direction="row" spacing={0.5} flexWrap="wrap">
      {statuses.map((key) => {
        const value = order?.[key];
        if (!value) return null;
        const label = labelMap[key][value] || `${key}: ${value}`;
        const color = colorMap[key][value] || 'default';
        return (
          <Chip
            key={`${key}-${value}`}
            size={compact ? 'small' : 'medium'}
            label={label}
            color={color}
            sx={{ mr: 0.5, mb: 0.5 }}
          />
        );
      })}
    </Stack>
  );
}
