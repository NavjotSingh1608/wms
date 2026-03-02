import api from './api';

export const listTransfers = (page = 1) =>
  api.get('/grade-transfer', { params: { page } });

export const createTransfer = (data: any) =>
  api.post('/grade-transfer', data);

export const approveTransfer = (id: string) =>
  api.put(`/grade-transfer/${id}/approve`);

export const rejectTransfer = (id: string, reason: string) =>
  api.put(`/grade-transfer/${id}/reject`, { reason });
