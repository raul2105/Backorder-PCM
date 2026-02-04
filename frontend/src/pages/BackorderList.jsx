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
  IconButton,
  Menu,
  FormControl,
  InputLabel,
  TableContainer,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FilterListIcon from '@mui/icons-material/FilterList';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import { backorderService } from '../services/api';
import StatusChips from '../components/StatusChips';

export default function BackorderList() {
  const [filters, setFilters] = useState({ status: '', search: '', order_number: '', customer_name: '', priority: '' });
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [filterAnchorEl, setFilterAnchorEl] = useState(null);
  const [filterColumn, setFilterColumn] = useState('');
  const [filterValue, setFilterValue] = useState('');
  const [sortAnchorEl, setSortAnchorEl] = useState(null);
  const [sortColumn, setSortColumn] = useState('');
  const [sortField, setSortField] = useState('priority');
  const [sortOrder, setSortOrder] = useState('asc');
  const [selected, setSelected] = useState([]);
  const [batchStatus, setBatchStatus] = useState('');
  const [isBatchUpdating, setIsBatchUpdating] = useState(false);
  const [updatingIds, setUpdatingIds] = useState({});
  const [openDetail, setOpenDetail] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  const { data, isLoading, refetch } = useQuery(
    ['backorders', filters, page, rowsPerPage, dateFrom, dateTo, sortField, sortOrder],
    () => backorderService.getAll({
      ...filters,
      page,
      page_size: rowsPerPage,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      sort: sortField,
      order: sortOrder
    }),
    { refetchInterval: 300000, keepPreviousData: true }
  );

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
    setPage(1);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage + 1);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(1);
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelected(orders.map(o => o.id));
    } else {
      setSelected([]);
    }
  };

  const handleSelect = (id) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const openFilterMenu = (event, column) => {
    setFilterAnchorEl(event.currentTarget);
    setFilterColumn(column);
    setFilterValue(filters[column] || '');
  };

  const closeFilterMenu = () => {
    setFilterAnchorEl(null);
    setFilterColumn('');
    setFilterValue('');
  };

  const applyColumnFilter = () => {
    if (filterColumn) {
      setFilters({ ...filters, [filterColumn]: filterValue });
      setPage(1);
    }
    closeFilterMenu();
  };

  const clearColumnFilter = () => {
    if (filterColumn) {
      setFilters({ ...filters, [filterColumn]: '' });
      setPage(1);
    }
    closeFilterMenu();
  };

  const openSortMenu = (event, column) => {
    setSortAnchorEl(event.currentTarget);
    setSortColumn(column);
  };

  const closeSortMenu = () => {
    setSortAnchorEl(null);
    setSortColumn('');
  };

  const applySort = (field, order) => {
    setSortField(field);
    setSortOrder(order);
    setPage(1);
    closeSortMenu();
  };

  const handleDateChange = (field, value) => {
    if (field == 'from') {
      setDateFrom(value);
    } else {
      setDateTo(value);
    }
    setPage(1);
  };

  const statusOptions = [
    { value: 'pending', label: 'Pendiente' },
    { value: 'in_production', label: 'En Produccion' },
    { value: 'ready', label: 'Listo' },
    { value: 'shipped', label: 'Enviado' },
    { value: 'delivered', label: 'Entregado' },
  ];

  const handleUpdateStatus = async (id, status) => {
    setUpdatingIds(prev => ({ ...prev, [id]: true }));
    try {
      await backorderService.updateStatus(id, status);
      await refetch();
    } catch {
    } finally {
      setUpdatingIds(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleUpdatePriority = async (id, priority) => {
    setUpdatingIds(prev => ({ ...prev, [id]: true }));
    try {
      await backorderService.updatePriority(id, priority);
      await refetch();
    } catch {
    } finally {
      setUpdatingIds(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleBatchUpdate = async () => {
    if (!batchStatus || selected.length == 0) return;
    setIsBatchUpdating(true);
    try {
      await backorderService.batchUpdateStatus(selected, batchStatus);
      setSelected([]);
      setBatchStatus('');
      await refetch();
    } catch {
    } finally {
      setIsBatchUpdating(false);
    }
  };

  const orders = data?.items || [];
  const total = data?.total || 0;

  if (isLoading && !data) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography variant="body2" color="textSecondary" gutterBottom>
          Cargando backorders...
        </Typography>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Planeación de Backorders
      </Typography>

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
                {statusOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Fecha Orden Desde"
              type="date"
              value={dateFrom}
              onChange={(e) => handleDateChange('from', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Fecha Orden Hasta"
              type="date"
              value={dateTo}
              onChange={(e) => handleDateChange('to', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
        {selected.length > 0 && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <Typography variant="body2">
              Acciones en lote: {selected.length} seleccionadas
            </Typography>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Nuevo estado</InputLabel>
              <Select
                value={batchStatus}
                onChange={(e) => setBatchStatus(e.target.value)}
                label="Nuevo estado"
              >
                <MenuItem value="">Seleccionar</MenuItem>
                {statusOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              disabled={!batchStatus || isBatchUpdating}
              onClick={handleBatchUpdate}
            >
              Aplicar
            </Button>
          </Box>
        )}
      </Paper>

      <Menu
        anchorEl={filterAnchorEl}
        open={Boolean(filterAnchorEl)}
        onClose={closeFilterMenu}
      >
        <Box sx={{ p: 2, minWidth: 220 }}>
          {filterColumn === 'status' && (
            <FormControl fullWidth size="small">
              <InputLabel>Estado</InputLabel>
              <Select
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
                label="Estado"
              >
                <MenuItem value="">Todos</MenuItem>
                {statusOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          {filterColumn === 'priority' && (
            <FormControl fullWidth size="small">
              <InputLabel>Prioridad</InputLabel>
              <Select
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
                label="Prioridad"
              >
                <MenuItem value="">Todas</MenuItem>
                {[1, 2, 3, 4].map(p => (
                  <MenuItem key={p} value={String(p)}>Prioridad {p}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          {filterColumn !== 'status' && filterColumn !== 'priority' && (
            <TextField
              fullWidth
              size="small"
              label="Filtro"
              value={filterValue}
              onChange={(e) => setFilterValue(e.target.value)}
            />
          )}
          <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
            <Button size="small" onClick={clearColumnFilter}>Limpiar</Button>
            <Button size="small" variant="contained" onClick={applyColumnFilter}>Aplicar</Button>
          </Box>
        </Box>
      </Menu>

      <Menu
        anchorEl={sortAnchorEl}
        open={Boolean(sortAnchorEl)}
        onClose={closeSortMenu}
      >
        <Box sx={{ p: 1, minWidth: 200 }}>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 1 }}>
            Ordenar por
          </Typography>
          {sortColumn && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button size="small" onClick={() => applySort(sortColumn, 'asc')}>Ascendente</Button>
              <Button size="small" onClick={() => applySort(sortColumn, 'desc')}>Descendente</Button>
            </Box>
          )}
        </Box>
      </Menu>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={orders.length > 0 && selected.length === orders.length}
                  indeterminate={selected.length > 0 && selected.length < orders.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell><strong>Orden</strong>
                <IconButton size="small" onClick={(e) => openFilterMenu(e, 'order_number')}>
                  <FilterListIcon fontSize="inherit" />
                </IconButton>
                <IconButton size="small" onClick={(e) => openSortMenu(e, 'order_number')}>
                  <SwapVertIcon fontSize="inherit" />
                </IconButton>
              </TableCell>
              <TableCell><strong>Cliente</strong>
                <IconButton size="small" onClick={(e) => openFilterMenu(e, 'customer_name')}>
                  <FilterListIcon fontSize="inherit" />
                </IconButton>
                <IconButton size="small" onClick={(e) => openSortMenu(e, 'customer_name')}>
                  <SwapVertIcon fontSize="inherit" />
                </IconButton>
              </TableCell>
              <TableCell><strong>Fecha Orden</strong>
                <IconButton size="small" onClick={(e) => openSortMenu(e, 'order_date')}>
                  <SwapVertIcon fontSize="inherit" />
                </IconButton>
              </TableCell>
              <TableCell><strong>Fecha Promesa</strong>
                <IconButton size="small" onClick={(e) => openSortMenu(e, 'promised_date')}>
                  <SwapVertIcon fontSize="inherit" />
                </IconButton>
              </TableCell>
              <TableCell><strong>Estado</strong>
                <IconButton size="small" onClick={(e) => openFilterMenu(e, 'status')}>
                  <FilterListIcon fontSize="inherit" />
                </IconButton>
                <IconButton size="small" onClick={(e) => openSortMenu(e, 'status')}>
                  <SwapVertIcon fontSize="inherit" />
                </IconButton>
              </TableCell>
              <TableCell><strong>Prioridad</strong>
                <IconButton size="small" onClick={(e) => openFilterMenu(e, 'priority')}>
                  <FilterListIcon fontSize="inherit" />
                </IconButton>
                <IconButton size="small" onClick={(e) => openSortMenu(e, 'priority')}>
                  <SwapVertIcon fontSize="inherit" />
                </IconButton>
              </TableCell>
              <TableCell><strong>Acciones</strong></TableCell>
            </TableRow>
          </TableHead>
                    <TableBody>
            {orders.map(order => (
              <TableRow key={order.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.includes(order.id)}
                    onChange={() => handleSelect(order.id)}
                  />
                </TableCell>
                <TableCell>{order.order_number}</TableCell>
                <TableCell>{order.customer_name}</TableCell>
                <TableCell>
                  {order.order_date ? format(new Date(order.order_date), 'dd/MM/yyyy') : '-'}
                </TableCell>
                <TableCell>
                  {order.promised_date ? format(new Date(order.promised_date), 'dd/MM/yyyy') : '-'}
                </TableCell>
                <TableCell>
                  <Chip label={order.status} size="small" />
                </TableCell>
                <TableCell>{order.priority || 3}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                      <Select
                        value={order.status || ''}
                        onChange={(e) => handleUpdateStatus(order.id, e.target.value)}
                        disabled={!!updatingIds[order.id]}
                      >
                        {statusOptions.map(option => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl size="small" sx={{ minWidth: 110 }}>
                      <Select
                        value={order.priority || 3}
                        onChange={(e) => handleUpdatePriority(order.id, Number(e.target.value))}
                        disabled={!!updatingIds[order.id]}
                      >
                        {[1, 2, 3, 4].map(p => (
                          <MenuItem key={p} value={p}>Prioridad {p}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {orders.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No hay backorders
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={total}
          rowsPerPage={rowsPerPage}
          page={page - 1}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Filas por página:"
        />
      </TableContainer>
    </Box>
  );
}
