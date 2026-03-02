import api from './api';

export const listFinishedGoods = (page = 1, stage?: string) =>
  api.get('/finished-goods', { params: { page, stage } });

export const createFinishedGood = (data: any) =>
  api.post('/finished-goods', data);

export const verifyFinishedGood = (id: string, data: any) =>
  api.put(`/finished-goods/${id}/verify`, data);

export const receiveFinishedGood = (id: string) =>
  api.put(`/finished-goods/${id}/receive`);

export const dispatchFinishedGood = (id: string, data: any) =>
  api.put(`/finished-goods/${id}/dispatch`, data);

export const generateShipperLabel = (id: string) =>
  api.get(`/finished-goods/${id}/shipper-label`);
