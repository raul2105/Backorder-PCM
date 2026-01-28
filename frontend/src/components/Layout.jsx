import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Switch,
  FormControlLabel,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Assignment as AssignmentIcon,
  Inventory as InventoryIcon,
  PrecisionManufacturing as PrecisionIcon,
  LocalShipping as LocalShippingIcon,
  Logout as LogoutIcon,
  Science as ScienceIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { authService, testModeService } from '../services/api';

const drawerWidth = 240;

function getMenuItems(user) {
  const items = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Planeación', icon: <AssignmentIcon />, path: '/backorder' },
    { text: 'Crear Orden', icon: <AddIcon />, path: '/backorder/new' },
    { text: 'Materiales', icon: <InventoryIcon />, path: '/materials' },
    { text: 'Producción', icon: <PrecisionIcon />, path: '/production' },
    { text: 'Logística', icon: <LocalShippingIcon />, path: '/logistics' },
  ];
  if (user?.role === 'admin') {
    items.push({ text: 'Usuarios', icon: <AssignmentIcon />, path: '/admin/users' });
    items.push({ text: 'Red', icon: <DashboardIcon />, path: '/admin/network' });
  }
  return items;
}

export default function Layout() {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [testMode, setTestMode] = React.useState(() => localStorage.getItem('testMode') === 'true');
  const [openTestDialog, setOpenTestDialog] = React.useState(false);
  const [testStatus, setTestStatus] = React.useState(null);
  const [currentUser, setCurrentUser] = React.useState(() => {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  });
  const navigate = useNavigate();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleTestModeToggle = async (event) => {
    const newValue = event.target.checked;
    
    if (newValue) {
      // Al activar, mostrar diálogo de opciones
      setOpenTestDialog(true);
    } else {
      // Al desactivar, simplemente quitar modo prueba
      setTestMode(false);
      localStorage.setItem('testMode', 'false');
      window.location.reload(); // Recargar para aplicar cambios
    }
  };

  const handleInitTestData = async () => {
    try {
      // Activar bandera de modo prueba ANTES de llamar al endpoint
      // para que el interceptor agregue el header X-Test-Mode
      setTestMode(true);
      localStorage.setItem('testMode', 'true');
      const result = await testModeService.init();
      setOpenTestDialog(false);
      window.location.reload(); // Recargar para aplicar cambios
    } catch (error) {
      // Revertir bandera si falló
      setTestMode(false);
      localStorage.setItem('testMode', 'false');
      alert('Error inicializando datos de prueba: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleStartEmpty = () => {
    // Activa modo pruebas inmediatamente para que el header se incluya
    setTestMode(true);
    localStorage.setItem('testMode', 'true');
    setOpenTestDialog(false);
    window.location.reload();
  };

  const handleResetTestData = async () => {
    if (confirm('¿Resetear todos los datos de prueba al estado original del CSV?')) {
      try {
        await testModeService.reset();
        window.location.reload();
      } catch (error) {
        alert('Error reseteando datos: ' + (error.response?.data?.error || error.message));
      }
    }
  };

  const items = getMenuItems(currentUser);

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Backorder PCM
        </Typography>
      </Toolbar>
      <Divider />
      
      {/* Toggle Modo Pruebas */}
      {currentUser?.role === 'admin' && (
        <Box sx={{ p: 2 }}>
          <FormControlLabel
            control={
              <Switch 
                checked={testMode} 
                onChange={handleTestModeToggle}
                color="warning"
              />
            }
            label={
              <Box display="flex" alignItems="center" gap={0.5}>
                <ScienceIcon fontSize="small" />
                <Typography variant="body2">Modo Pruebas</Typography>
              </Box>
            }
          />
          {testMode && (
            <Button 
              size="small" 
              onClick={handleResetTestData}
              sx={{ mt: 1, fontSize: '0.7rem' }}
            >
              Resetear Datos
            </Button>
          )}
        </Box>
      )}
      <Divider />
      
      <List>
        {items.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton onClick={() => navigate(item.path)}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      
      {/* Usuario Actual */}
      {currentUser && (
        <Box sx={{ p: 2, bgcolor: '#f5f5f5' }}>
          <Typography variant="caption" display="block" color="text.secondary">
            Usuario Actual:
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 'bold', mt: 0.5 }}>
            {currentUser.username || 'Usuario'}
          </Typography>
          {currentUser.role && (
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
              Rol: <strong>{currentUser.role}</strong>
            </Typography>
          )}
        </Box>
      )}
      <Divider />
      
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={handleLogout}>
            <ListItemIcon>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText primary="Cerrar Sesión" />
          </ListItemButton>
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          bgcolor: testMode ? '#ff6b35' : 'primary.main',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Sistema de Gestión de Backorder
          </Typography>
          {testMode && (
            <Box display="flex" alignItems="center" gap={1}>
              <ScienceIcon />
              <Typography variant="body2" fontWeight="bold">
                MODO PRUEBAS
              </Typography>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        {testMode && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <strong>Modo de Pruebas Activo:</strong> Los cambios no afectarán los datos reales. 
            Todos los pedidos tienen el prefijo TEST-.
          </Alert>
        )}
        <Outlet />
      </Box>

      {/* Diálogo de inicialización de datos de prueba */}
      <Dialog open={openTestDialog} onClose={() => setOpenTestDialog(false)}>
        <DialogTitle>Activar Modo de Pruebas</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            ¿Deseas cargar los datos de ejemplo del CSV para empezar a probar?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            • <strong>Cargar desde CSV:</strong> Importa los pedidos del archivo BO_Sample.csv con prefijo TEST-
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • <strong>Empezar vacío:</strong> Activa el modo sin cargar datos (puedes agregar manualmente)
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTestDialog(false)}>Cancelar</Button>
          <Button onClick={handleStartEmpty} variant="outlined">
            Empezar Vacío
          </Button>
          <Button onClick={handleInitTestData} variant="contained" color="warning">
            Cargar desde CSV
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
