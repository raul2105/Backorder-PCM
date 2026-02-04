/**
 * Servicio de API - Maneja todas las llamadas al backend
 */

import axios from 'axios';

const API_BASE_URL = `${window.location.origin}/api`;

// Configurar interceptores de Axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

let inMemoryToken = null;

const getCookieToken = () => {
  const match = document.cookie.match(/(?:^|; )bo_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
};

const setCookieToken = (token) => {
  if (token) {
    document.cookie = `bo_token=${encodeURIComponent(token)}; path=/; SameSite=Lax`;
  } else {
    document.cookie = 'bo_token=; Max-Age=0; path=/; SameSite=Lax';
  }
};

const setToken = (token) => {
  inMemoryToken = token || null;
  if (token) {
    localStorage.setItem('token', token);
    sessionStorage.setItem('token', token);
    setCookieToken(token);
    api.defaults.headers.Authorization = `Bearer ${token}`;
    if (api.defaults.headers.common) {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;
    }
  } else {
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    setCookieToken(null);
    delete api.defaults.headers.Authorization;
    if (api.defaults.headers.common) {
      delete api.defaults.headers.common.Authorization;
    }
  }
};

const getStoredToken = () =>
  inMemoryToken || localStorage.getItem('token') || sessionStorage.getItem('token') || getCookieToken();

const bootToken = localStorage.getItem('token') || sessionStorage.getItem('token');
if (bootToken) {
  setToken(bootToken);
}

// Interceptor para agregar token a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = getStoredToken();
    if (token) {
      if (!config.headers) {
        config.headers = {};
      }
      if (typeof config.headers.set === 'function') {
        config.headers.set('Authorization', `Bearer ${token}`);
      } else {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => {
    if (response?.config?.url?.includes('/auth/login') && response.data?.access_token) {
      setToken(response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 403 && error.response?.data?.must_change_password) {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const updatedUser = { ...user, must_change_password: true };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      window.dispatchEvent(new Event('storage'));
      window.location.href = '/change-password';
    }
    if (error.response?.status === 401) {
      const headerAuth = error.config?.headers?.Authorization || error.config?.headers?.authorization;
      const hasAuthHeader = Boolean(headerAuth);
      const hasStoredToken = Boolean(getStoredToken());
      if (hasAuthHeader || hasStoredToken) {
        setToken(null);
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Servicios de Autenticación
export const authService = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.access_token) {
      setToken(response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }
    return response.data;
  },

  changePassword: async (currentPassword, newPassword) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const updatedUser = { ...user, must_change_password: false };
    localStorage.setItem('user', JSON.stringify(updatedUser));
    return response.data;
  },

  logout: () => {
    setToken(null);
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

  getInProgressOrders: async (filters = {}) => {
    const response = await api.get('/production/in-progress-orders', { params: filters });
    return response.data;
  },

  createLog: async (logData) => {
    const response = await api.post('/production/log', logData);
    return response.data;
  },

  ocrValidate: async (orderId, imageFile) => {
    const form = new FormData();
    form.append('image', imageFile);
    const response = await api.post(`/production/order/${orderId}/ocr-validate`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
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
  },

  ocrValidateShipment: async (orderId, imageFile) => {
    const form = new FormData();
    form.append('image', imageFile);
    const response = await api.post(`/logistics/shipment/${orderId}/ocr-validate`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
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
  },
  purgeOrders: async (payload) => {
    const res = await api.post('/admin/purge/orders', payload);
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

export default api;
