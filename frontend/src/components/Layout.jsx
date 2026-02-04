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
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Assignment as AssignmentIcon,
  Inventory as InventoryIcon,
  PrecisionManufacturing as PrecisionIcon,
  LocalShipping as LocalShippingIcon,
  Logout as LogoutIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { authService } from '../services/api';

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

  const items = getMenuItems(currentUser);

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Backorder PCM
        </Typography>
      </Toolbar>
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
          bgcolor: 'primary.main',
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
        
          
        <Outlet />
      </Box>

      
    </Box>
  );
}
