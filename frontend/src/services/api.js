/**
 * Servicio de API - Maneja todas las llamadas al backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Configurar interceptores de Axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para agregar token a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Agregar header de modo pruebas si está activo
    const testMode = localStorage.getItem('testMode') === 'true';
    if (testMode) {
      config.headers['X-Test-Mode'] = 'true';
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Servicios de Autenticación
export const authService = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  }
};

// Servicios de Backorder
export const backorderService = {
  getAll: async (filters = {}) => {
    const response = await api.get('/backorder', { params: filters });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/backorder/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/backorder', data);
    return response.data;
  },

  updatePriority: async (id, priority) => {
    const response = await api.put(`/backorder/${id}/priority`, { priority });
    return response.data;
  },

  updateStatus: async (id, status) => {
    const response = await api.put(`/backorder/${id}/status`, { status });
    return response.data;
  },

  updateDepartmentStatus: async (id, department, status) => {
    const response = await api.put(`/backorder/${id}/department-status`, { department, status });
    return response.data;
  },

  updateItem: async (orderId, itemId, data) => {
    const response = await api.put(`/backorder/${orderId}/items/${itemId}`, data);
    return response.data;
  },

  batchUpdateStatus: async (orderIds, status) => {
    const response = await api.put('/backorder/batch/update-status', { order_ids: orderIds, status });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/backorder/stats');
    return response.data;
  }
};

// Servicios de Materiales
export const materialService = {
  getAll: async (filters = {}) => {
    const response = await api.get('/materials', { params: filters });
    return response.data;
  },

  getAlerts: async () => {
    const response = await api.get('/materials/alerts');
    return response.data;
  }
};

// Servicios de Producción
export const productionService = {
  getLogs: async (filters = {}) => {
    const response = await api.get('/production/logs', { params: filters });
    return response.data;
  },

  createLog: async (logData) => {
    const response = await api.post('/production/log', logData);
    return response.data;
  }
};

// Servicios de Logística
export const logisticsService = {
  getPendingShipments: async (filters = {}) => {
    const response = await api.get('/logistics/pending-shipments', { params: filters });
    return response.data;
  },

  getShippedOrders: async (filters = {}) => {
    const response = await api.get('/logistics/shipped', { params: filters });
    return response.data;
  },

  updateShipment: async (orderId, trackingNumber, carrier) => {
    const response = await api.put(`/logistics/shipment/${orderId}`, { tracking_number: trackingNumber, carrier });
    return response.data;
  }
};

// Servicios de Dashboard
export const dashboardService = {
  getOverview: async () => {
    const response = await api.get('/dashboard/overview');
    return response.data;
  },

  getRecentActivity: async () => {
    const response = await api.get('/dashboard/recent-activity');
    return response.data;
  }
};

// Servicios de Administración (solo admin)
export const adminService = {
  listUsers: async () => {
    const res = await api.get('/admin/users');
    return res.data;
  },
  createUser: async (data) => {
    const res = await api.post('/admin/users', data);
    return res.data;
  },
  updateUser: async (id, data) => {
    const res = await api.put(`/admin/users/${id}`, data);
    return res.data;
  },
  listAudit: async () => {
    const res = await api.get('/admin/audit');
    return res.data;
  }
};

// Configuración del Sistema
export const settingsService = {
  getNetwork: async () => {
    const res = await api.get('/settings/network');
    return res.data;
  },
  updateNetwork: async (allowed_ips) => {
    const res = await api.put('/settings/network', { allowed_ips });
    return res.data;
  }
};

// Modo de Pruebas
export const testModeService = {
  getStatus: async () => {
    const res = await api.get('/test/status');
    return res.data;
  },
  init: async () => {
    const res = await api.post('/test/init');
    return res.data;
  },
  reset: async () => {
    const res = await api.post('/test/reset');
    return res.data;
  },
  clear: async () => {
    const res = await api.post('/test/clear');
    return res.data;
  }
};

export default api;
