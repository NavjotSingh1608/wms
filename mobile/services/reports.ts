import api from './api';

export const getStockReport = (params?: {
  page?: number;
  status?: string;
  search?: string;
}) => api.get('/reports/stock', { params });

export const getStockSummary = () => api.get('/reports/stock/summary');

export const exportStockCSV = (params?: { status?: string; search?: string }) =>
  api.get('/reports/stock/export', { params, responseType: 'blob' });
