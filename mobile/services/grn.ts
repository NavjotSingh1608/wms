import api from './api';

export const createGRN = (data: any) => api.post('/grn', data);

export const listGRNs = (page = 1, status?: string) =>
  api.get('/grn', { params: { page, status } });

export const getGRN = (id: string) => api.get(`/grn/${id}`);

export const updateRack = (id: string, rack_no: string) =>
  api.put(`/grn/${id}/rack`, { rack_no });

export const scanQR = (grnId: string) => api.get(`/qr/scan/${grnId}`);
