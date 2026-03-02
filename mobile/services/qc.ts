import api from './api';

export const createSampling = (data: any) => api.post('/qc/sampling', data);

export const createDecision = (data: any) => api.post('/qc/decision', data);

export const listPendingSampling = (page = 1) =>
  api.get('/grn', { params: { page, status: 'QUARANTINE' } });

export const listPendingDecision = (page = 1) =>
  api.get('/grn', { params: { page, status: 'UNDER_TEST' } });
