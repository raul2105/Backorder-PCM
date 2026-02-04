import React from 'react';
import { useQuery } from 'react-query';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Warning as WarningIcon,
  PrecisionManufacturing as PrecisionIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { dashboardService } from '../services/api';

export default function Dashboard() {
  const { data: overview, isLoading } = useQuery('dashboard-overview', 
    dashboardService.getOverview,
    { refetchInterval: 30000 }
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const stats = [
    {
      title: 'Ordenes en Backorder',
      value: overview?.backorders?.total || 0,
      icon: <AssignmentIcon sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'Ordenes Urgentes (7 dias)',
      value: overview?.backorders?.urgent || 0,
      icon: <WarningIcon sx={{ fontSize: 40 }} />,
      color: '#d32f2f',
    },
    {
      title: 'Ordenes en Produccion',
      value: overview?.production?.in_progress || 0,
      icon: <PrecisionIcon sx={{ fontSize: 40 }} />,
      color: '#f57c00',
    },
    {
      title: 'Ordenes Completadas (Semana)',
      value: overview?.completed?.this_week || 0,
      icon: <CheckCircleIcon sx={{ fontSize: 40 }} />,
      color: '#388e3c',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>
                    {stat.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Alertas de Inventario
            </Typography>
            <Typography color="textSecondary">
              {overview?.inventory?.low_stock_alerts || 0} materiales con stock bajo
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Producción de Hoy
            </Typography>
            <Typography color="textSecondary">
              {overview?.production?.logs_today || 0} registros de producción
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
