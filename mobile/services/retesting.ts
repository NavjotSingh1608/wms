import api from './api';

export const getRetestingQueue = (page = 1) =>
  api.get('/retesting', { params: { page } });

export const initiateRetesting = (grnId: string) =>
  api.post(`/retesting/${grnId}/initiate`);

export const getRetestHistory = (grnId: string) =>
  api.get(`/retesting/${grnId}/history`);
